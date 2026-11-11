import datetime
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import engine
import study
from test_mastery import NOW, PREREQUISITE, TOPIC, FixedDateTime, LearningAPITestCase


FOUNDATION = "ic_desigualdades"
PATH = "/api/study"
SEED = 1107


class StudyTests(LearningAPITestCase):
    def open_lesson(self, topic_id=TOPIC, task_type="lesson"):
        with patch.object(engine.random, "getrandbits", return_value=SEED):
            return self.request(PATH, {
                "kind": "lesson", "action": "open", "topic_id": topic_id, "task_type": task_type,
            })

    def lesson_step(self, session, **kwargs):
        return {
            "kind": "lesson", "action": "advance", "slot": session["slot"], "session_id": session["id"],
            "step": session["step"], "answered": len(session["answers"]), **kwargs,
        }

    def resume(self, session, **kwargs):
        return self.request(PATH, {**self.lesson_step(session), "action": "resume", **kwargs})

    def confirm_lesson_answer(self, session, correct):
        question = session["topic"]["questions"][session["step"] - 1]
        choice = question["correct_index"]
        if not correct:
            choice = (choice + 1) % len(question["options"])
        return self.request(PATH, self.lesson_step(session, choice=choice))

    def finish_practice(self, response, correct):
        session = response["session"]
        for _ in session["topic"]["questions"]:
            response = self.confirm_lesson_answer(session, correct)
            response = self.request(PATH, self.lesson_step(response["session"]))
            session = response["session"]
        return response

    def open_quiz(self, **kwargs):
        with patch.object(engine.random, "getrandbits", return_value=SEED):
            return self.request(PATH, {"kind": "quiz", "action": "open", **kwargs})

    def quiz_answer(self, response, correct):
        session = response["session"]
        progress = response["state"]["backup_snapshot"]["study"]["progress"]
        variant = progress["quiz"]["variants"][session["answered"]]
        question = study.quiz_question(variant)
        choice = question["correct_index"]
        if not correct:
            choice = (choice + 1) % len(question["options"])
        self.assertEqual(session["question"], {key: question[key] for key in ("prompt", "options")})
        return {
            "kind": "quiz", "action": "advance", "session_id": session["id"],
            "answered": session["answered"], "choice": choice,
        }

    def test_lesson_resume_with_saved_feedback_and_atomic_idempotent_completion(self):
        opened = self.open_lesson()
        original = opened["session"]
        self.assertEqual(original["step"], 0)
        self.assertEqual(original["topic"], engine.get_topic_lesson_payload(TOPIC, seed=SEED))
        state = opened["state"]
        limits = next(topic for topic in state["topics"] if topic["id"] == TOPIC)
        self.assertEqual(limits["prereqs"], [PREREQUISITE])
        self.assertEqual(limits["met_prereqs"], [])
        self.assertEqual(next(course for course in state["courses"] if course["id"] == "IC")["progress_pct"], 0)
        first = self.request(PATH, self.lesson_step(original))["session"]
        answered = self.confirm_lesson_answer(first, False)
        self.assertEqual(answered["session"]["step"], 1)
        self.assertEqual(answered["state"]["study"]["lessons"][0]["answered"], 1)

        # Una lección de otro tema deja intacta la sesión anterior.
        self.open_lesson(PREREQUISITE)
        FixedDateTime.current = NOW + datetime.timedelta(days=2)
        stale = opened["state"]["backup_snapshot"]
        self.assertEqual(self.resume(first, client_backup=stale)["session"], answered["session"])
        self.assertEqual(self.open_lesson()["session"], answered["session"])
        saved = self.request("/api/backup")
        with patch.object(engine, "DB_PATH", os.path.join(os.path.dirname(engine.DB_PATH), "restored.db")):
            self.request("/api/backup", saved)
            self.assertEqual(self.resume(first)["session"], answered["session"])

        session = answered["session"]
        for _ in original["topic"]["questions"][1:]:
            session = self.request(PATH, self.lesson_step(session))["session"]
            session = self.confirm_lesson_answer(session, True)["session"]
        final_payload = self.lesson_step(session, client_backup=stale)
        with patch.object(engine, "_activity_writes", return_value=[("INSERT INTO missing_table VALUES (1)", ())]):
            with self.assertRaises(sqlite3.OperationalError):
                engine.advance_study(final_payload)
        self.assertIsNone(self.resume(first)["session"]["result"])
        self.assertEqual(self.request("/api/state")["profile"]["total_xp"], 0)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: self.request(PATH, final_payload), range(2)))
        self.assertEqual(outcomes[0]["session"], outcomes[1]["session"])
        result = outcomes[0]["session"]["result"]
        self.assertTrue(result["passed"])
        state = self.request("/api/state", {"client_backup": stale})
        self.assertEqual(state["profile"]["total_xp"], result["xp_earned"])
        self.assertEqual(state["profile"]["today_xp"], result["xp_earned"])
        self.assertEqual(len(state["backup_snapshot"]["xp_log"]), 1)
        self.assertEqual(state["study"]["last_lesson"]["id"], original["id"])
        self.assertEqual(self.resume(first)["session"]["result"], result)
        self.assertEqual(len(state["activity_7d"]), 7)
        self.assertEqual(state["activity_7d"][-1], {
            "date": FixedDateTime.current.date().isoformat(), "xp": result["xp_earned"], "sessions": 1,
        })
        FixedDateTime.current += datetime.timedelta(days=7)
        later = self.request("/api/state")
        self.assertTrue(all(day["sessions"] == 0 and day["xp"] == 0 for day in later["activity_7d"]))
        self.assertEqual(later["profile"]["total_xp"], result["xp_earned"])
        legacy = {key: value for key, value in later["backup_snapshot"].items() if key != "study"}
        with patch.object(engine, "DB_PATH", os.path.join(os.path.dirname(engine.DB_PATH), "legacy.db")):
            imported = self.request("/api/backup", legacy)["state"]
            self.assertEqual(imported["profile"]["total_xp"], result["xp_earned"])
            self.assertEqual(imported["study"]["lessons"], [])
            self.assertEqual(imported["backup_snapshot"]["topic_state"], legacy["topic_state"])

    def test_quiz_interleaves_seen_topics_without_reusing_prompts_and_schedules_each_miss(self):
        self.request(PATH, {"kind": "quiz", "action": "open"}, status="400 Bad Request")
        # Una respuesta confirmada cuenta como tema visto aunque todavía no haya maestría.
        lesson = self.open_lesson(FOUNDATION)["session"]
        first = self.request(PATH, self.lesson_step(lesson))["session"]
        self.confirm_lesson_answer(first, False)
        self.request(PATH, {"kind": "quiz", "action": "open"}, status="400 Bad Request")
        self.request("/api/complete", {"topic_id": PREREQUISITE, "correct_count": 4, "total_count": 4})
        self.request("/api/complete", {"topic_id": TOPIC, "correct_count": 4, "total_count": 4})
        before = self.request("/api/state")

        quiz = self.open_quiz()
        snapshot = quiz["state"]["backup_snapshot"]
        variants = snapshot["study"]["progress"]["quiz"]["variants"]
        self.assertEqual({variant["topic_id"] for variant in variants}, {FOUNDATION, PREREQUISITE, TOPIC})
        first_prompt = quiz["session"]["question"]["prompt"]
        allocated = {study.prompt_key(study.quiz_question(variant)["prompt"]) for variant in variants}
        self.assertFalse(allocated & set(before["backup_snapshot"]["study"]["progress"]["seen"]))
        self.assertNotIn("results", quiz["session"])
        self.assertNotIn("correct_index", quiz["session"]["question"])
        self.assertNotIn("hint", quiz["session"]["question"])

        self.assertEqual(self.open_quiz()["session"]["question"]["prompt"], first_prompt)
        for index in range(2):
            quiz = self.request(PATH, self.quiz_answer(quiz, index == 0))
        self.assertNotIn("results", quiz["session"])
        with patch.object(engine, "DB_PATH", os.path.join(os.path.dirname(engine.DB_PATH), "quiz.db")):
            self.request("/api/backup", quiz["state"]["backup_snapshot"])
            self.assertEqual(self.open_quiz()["session"], quiz["session"])
        final_payload = self.quiz_answer(quiz, False)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: self.request(PATH, final_payload), range(2)))
        result = outcomes[0]["session"]
        self.assertEqual(result, outcomes[1]["session"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["xp_earned"], 1)
        errors = {item["topic_id"] for item in result["results"] if not item["correct"]}
        state = outcomes[0]["state"]
        self.assertEqual(set(state["study"]["quiz_reviews"]), errors)
        self.assertEqual({task["topic_id"] for task in state["recommendations"] if task["task_type"] == "quiz_review"}, errors)
        self.assertEqual(before["backup_snapshot"]["topic_state"], state["backup_snapshot"]["topic_state"])
        self.assertEqual(state["profile"]["total_xp"], before["profile"]["total_xp"] + 1)
        self.assertEqual(state["activity_7d"][-1]["sessions"], before["activity_7d"][-1]["sessions"] + 1)

        review_topic = sorted(errors)[0]
        failed = self.finish_practice(self.open_lesson(review_topic, "quiz_review"), False)
        self.assertIn(review_topic, failed["state"]["study"]["quiz_reviews"])
        retry = self.open_lesson(review_topic, "quiz_review")
        self.assertEqual(retry["session"]["step"], 1)
        prompts = {study.prompt_key(question["prompt"]) for question in retry["session"]["topic"]["questions"]}
        self.assertNotIn(state["backup_snapshot"]["study"]["progress"]["quiz_reviews"][review_topic], prompts)
        passed = self.finish_practice(retry, True)
        self.assertEqual(set(passed["state"]["study"]["quiz_reviews"]), errors - {review_topic})

        next_quiz = self.open_quiz(restart_from=result["id"])
        next_variants = next_quiz["state"]["backup_snapshot"]["study"]["progress"]["quiz"]["variants"]
        self.assertFalse(allocated & {study.prompt_key(study.quiz_question(variant)["prompt"]) for variant in next_variants})
        self.assertEqual(self.request(PATH, final_payload)["session"], next_quiz["session"])

        demo = self.request("/api/profile", {"preset_mode": "mid_sem1"})["state"]
        self.assertEqual(demo["study"]["quiz"]["id"], next_quiz["session"]["id"])
        self.request("/api/profile", {"preset_mode": "reset"})
        reset = self.request("/api/state", {"client_backup": demo["backup_snapshot"]})
        self.assertEqual(reset["study"]["quiz"]["status"], "idle")
        self.assertEqual(reset["study"]["quiz_reviews"], [])
        self.assertEqual(reset["profile"]["total_xp"], 0)
