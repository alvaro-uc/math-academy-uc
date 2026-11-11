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
            "step": session["step"], "answered": len(session["answers"]), "tracks_hint": True, **kwargs,
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
        for _ in session["topic"]["questions"][len(session["answers"]):]:
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

    def first_attempts(self):
        return self.request("/api/backup")["study"]["progress"]["first_attempts"]

    def test_first_attempt_survives_reload_duplicate_confirmation_and_backup(self):
        opened = self.open_lesson()
        first = self.request(PATH, self.lesson_step(opened["session"]))
        session = first["session"]
        question = session["topic"]["questions"][0]
        choice = (question["correct_index"] + 1) % len(question["options"])
        stale = first["state"]["backup_snapshot"]
        self.request(PATH, self.lesson_step(session, choice=True), status="400 Bad Request")
        self.request(PATH, self.lesson_step(session, action="hint"))
        self.assertEqual(self.first_attempts(), [])

        FixedDateTime.current = NOW + datetime.timedelta(days=2)
        resumed = self.resume(session, client_backup=stale)["session"]
        self.assertTrue(resumed["hint_used"])
        self.assertEqual(resumed["answers"], [])
        payload = self.lesson_step(resumed, choice=choice)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: self.request(PATH, payload), range(2)))
        attempt = {
            "session_id": session["id"], "topic_id": TOPIC, "task_type": "lesson", "question_index": 0,
            "prompt_key": study.prompt_key(question["prompt"]), "correct": False, "hint_used": True,
            "answered_ts": FixedDateTime.current.timestamp(),
        }
        for outcome in outcomes:
            snapshot = outcome["state"]["backup_snapshot"]
            self.assertEqual(snapshot["study"]["progress"]["first_attempts"], [attempt])
            self.assertEqual(snapshot["topic_state"], stale["topic_state"])
            self.assertEqual(snapshot["xp_log"], [])

        FixedDateTime.current += datetime.timedelta(minutes=5)
        changed_choice = self.lesson_step(session, choice=question["correct_index"], client_backup=stale)
        self.assertEqual(self.request(PATH, changed_choice)["session"]["answers"], [choice])
        self.assertEqual(self.first_attempts(), [attempt])
        saved = self.request("/api/backup")
        with patch.object(engine, "DB_PATH", os.path.join(os.path.dirname(engine.DB_PATH), "attempt.db")):
            self.request("/api/backup", saved)
            restored = self.resume(session)["session"]
            self.assertEqual(restored["answers"], [choice])
            self.assertEqual(self.first_attempts(), [attempt])
            second = self.request(PATH, self.lesson_step(restored))
            self.assertFalse(second["session"]["hint_used"])
            self.finish_practice(second, True)
            self.assertNotEqual(self.open_lesson()["session"]["id"], session["id"])
            history = self.first_attempts()
            self.assertEqual(history[0], attempt)
            self.assertEqual(len(history), len(session["topic"]["questions"]))
            self.assertTrue(all(item["correct"] and item["hint_used"] is False for item in history[1:]))

    def test_legacy_backup_preserves_answers_without_inventing_hint_history(self):
        opened = self.open_lesson()["session"]
        first = self.request(PATH, self.lesson_step(opened))["session"]
        answered = self.confirm_lesson_answer(first, True)["session"]
        second = self.request(PATH, self.lesson_step(answered))["session"]
        legacy = self.request("/api/backup")
        progress = legacy["study"]["progress"]
        progress.pop("first_attempts")
        progress["lessons"][second["slot"]].pop("hint_used")
        with patch.object(engine, "DB_PATH", os.path.join(os.path.dirname(engine.DB_PATH), "older.db")):
            restored = self.request("/api/backup", legacy)["state"]["backup_snapshot"]
            self.assertEqual(restored["topic_state"], legacy["topic_state"])
            self.assertEqual(restored["xp_log"], legacy["xp_log"])
            self.assertEqual(self.resume(second)["session"]["answers"], answered["answers"])
            self.assertEqual(self.first_attempts(), [])
            self.confirm_lesson_answer(second, True)
            attempt, = self.first_attempts()
            self.assertEqual(attempt["question_index"], 1)
            self.assertTrue(attempt["correct"])
            self.assertIsNone(attempt["hint_used"])

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
        with patch.object(engine, "_activity_writes", return_value=[("INSERT INTO missing_table VALUES (1)", ())]):
            with self.assertRaises(sqlite3.OperationalError):
                engine.advance_study(final_payload)
        self.assertEqual(self.open_quiz()["session"], quiz["session"])
        self.assertEqual(len(self.first_attempts()), 3)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: self.request(PATH, final_payload), range(2)))
        result = outcomes[0]["session"]
        self.assertEqual(result, outcomes[1]["session"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["xp_earned"], 1)
        errors = {item["topic_id"] for item in result["results"] if not item["correct"]}
        state = outcomes[0]["state"]
        attempts = [item for item in self.first_attempts() if item["session_id"] == result["id"]]
        self.assertEqual([item["question_index"] for item in attempts], [0, 1, 2])
        self.assertEqual([item["topic_id"] for item in attempts], [item["topic_id"] for item in result["results"]])
        self.assertEqual([item["correct"] for item in attempts], [True, False, False])
        self.assertTrue(all(item["task_type"] == "quiz" and item["hint_used"] is False for item in attempts))
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
        retry_session = retry["session"]
        self.assertEqual(self.request(PATH, self.lesson_step(retry_session, action="hint"))["session"], retry_session)
        prompts = {study.prompt_key(question["prompt"]) for question in retry["session"]["topic"]["questions"]}
        self.assertNotIn(state["backup_snapshot"]["study"]["progress"]["quiz_reviews"][review_topic], prompts)
        passed = self.finish_practice(retry, True)
        self.assertEqual(set(passed["state"]["study"]["quiz_reviews"]), errors - {review_topic})

        next_quiz = self.open_quiz(restart_from=result["id"])
        next_variants = next_quiz["state"]["backup_snapshot"]["study"]["progress"]["quiz"]["variants"]
        self.assertFalse(allocated & {study.prompt_key(study.quiz_question(variant)["prompt"]) for variant in next_variants})
        self.assertEqual(self.request(PATH, final_payload)["session"], next_quiz["session"])
        history = self.first_attempts()
        self.assertTrue(all(item in history for item in attempts))
        review_attempts = [item for item in history if item["session_id"] == retry_session["id"]]
        self.assertEqual(len(review_attempts), len(retry_session["topic"]["questions"]))
        self.assertTrue(all(item["hint_used"] is False for item in review_attempts))

        demo = self.request("/api/profile", {"preset_mode": "mid_sem1"})["state"]
        self.assertEqual(demo["study"]["quiz"]["id"], next_quiz["session"]["id"])
        self.request("/api/profile", {"preset_mode": "reset"})
        reset = self.request("/api/state", {"client_backup": demo["backup_snapshot"]})
        self.assertEqual(reset["study"]["quiz"]["status"], "idle")
        self.assertEqual(reset["study"]["quiz_reviews"], [])
        self.assertEqual(reset["profile"]["total_xp"], 0)
        self.assertEqual(self.first_attempts(), [])
