import datetime
import io
import json
import os
import random
import tempfile
import unittest
from unittest.mock import patch
from wsgiref.util import setup_testing_defaults

import app
import engine


TOPIC = "ic_limites"
DEPENDENT = "ic_continuidad_derivada"
PREREQUISITE = "ic_funciones"
DAY = 86400
NOW = datetime.datetime(2026, 11, 11, 15, tzinfo=datetime.timezone.utc)


class FixedDateTime(datetime.datetime):
    current = NOW

    @classmethod
    def now(cls, tz=None):
        return cls.current.astimezone(tz)


class FixedDate(datetime.date):
    @classmethod
    def today(cls):
        return FixedDateTime.current.date()


class LearningAPITestCase(unittest.TestCase):
    def setUp(self):
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch.dict(os.environ, {"APP_PASSWORD": "clave de prueba"}, clear=True))
        self.enterContext(patch.object(engine, "DB_PATH", os.path.join(tmp, "test.db")))
        self.enterContext(patch.object(engine.datetime, "datetime", FixedDateTime))
        self.enterContext(patch.object(engine.datetime, "date", FixedDate))
        self.enterContext(patch.object(FixedDateTime, "current", NOW))
        login = self.request("/api/auth/login", {"password": "clave de prueba"})
        self.token = login["token"]

    def request(self, path, payload=None, *, status="200 OK"):
        environ = {}
        setup_testing_defaults(environ)
        environ["PATH_INFO"], _, environ["QUERY_STRING"] = path.partition("?")
        environ["HTTP_AUTHORIZATION"] = f"Bearer {getattr(self, 'token', '')}"
        if payload is not None:
            body = json.dumps(payload).encode()
            environ.update(REQUEST_METHOD="POST", CONTENT_LENGTH=str(len(body)))
            environ["wsgi.input"] = io.BytesIO(body)
        statuses = []
        response = app.application(environ, lambda status, headers: statuses.append(status))
        self.assertEqual(statuses, [status], response)
        return json.loads(b"".join(response))


class MasteryTests(LearningAPITestCase):
    def complete(self, correct, total, task_type="lesson", snapshot=None, *, topic_id=TOPIC):
        response = self.request(
            "/api/complete",
            {
                "topic_id": topic_id,
                "correct_count": correct,
                "total_count": total,
                "task_type": task_type,
                "client_backup": snapshot,
            },
        )
        return response["result"], response["state"]

    def topic(self, state, topic_id):
        return next(topic for topic in state["topics"] if topic["id"] == topic_id)

    def stored(self, state, topic_id=TOPIC):
        return next(row for row in state["backup_snapshot"]["topic_state"] if row["topic_id"] == topic_id)

    def prepare_review(self, prerequisite_mastery=0.88, prerequisite_due=False):
        state = self.request("/api/state")
        self.stored(state).update(
            mastery=0.92,
            stability_days=8.0,
            repetitions=3,
            last_practiced_ts=NOW.timestamp() - 8 * DAY,
            next_review_ts=NOW.timestamp(),
        )
        self.stored(state, PREREQUISITE).update(
            mastery=prerequisite_mastery,
            stability_days=20.0,
            last_practiced_ts=NOW.timestamp() - (20 if prerequisite_due else 1) * DAY,
            next_review_ts=NOW.timestamp() + (0 if prerequisite_due else 19) * DAY,
        )
        engine.import_backup_payload(state["backup_snapshot"])
        return state["backup_snapshot"]

    def review_variant(self, topic_id, task_type, seed):
        with patch.object(engine.random, "getrandbits", return_value=seed):
            lesson = self.request(f"/api/topic/{topic_id}?task_type={task_type}")
        self.assertEqual(
            lesson, engine.get_topic_lesson_payload(topic_id, seed=seed, task_type=task_type)
        )
        return lesson["questions"]

    def task_for(self, state, topic_id=TOPIC):
        return next((task for task in state["recommendations"] if task["topic_id"] == topic_id), None)

    def test_on_time_and_overdue_success_use_the_same_retention_curve(self):
        baseline = self.prepare_review()
        questions = self.review_variant(TOPIC, "review", seed=1107)
        self.assertEqual(len(questions), 3)
        self.assertTrue(all(question["is_parametric"] for question in questions))
        self.assertNotEqual(questions, self.review_variant(TOPIC, "review", seed=1108))
        for late_days, expected_retention in ((0, 0.78), (8, 0.608)):
            with self.subTest(late_days=late_days):
                FixedDateTime.current = NOW + datetime.timedelta(days=late_days)
                engine.import_backup_payload(baseline)
                state = self.request("/api/state")
                self.assertEqual(self.topic(state, TOPIC)["retention"], expected_retention)
                self.assertTrue(self.topic(state, TOPIC)["due_for_review"])
                self.assertTrue(all(task["reason"] for task in state["recommendations"]))
                result, state = self.complete(len(questions), len(questions), "review")
                self.assertTrue(result["passed"])
                self.assertFalse(result["recovery_scheduled"])
                self.assertAlmostEqual(
                    self.stored(state)["next_review_ts"],
                    FixedDateTime.current.timestamp() + 21.6 * DAY,
                )

    def test_failed_review_gets_a_direct_retry_and_second_failure_gets_recovery(self):
        self.prepare_review()
        direct = self.review_variant(TOPIC, "review", seed=12)
        result, state = self.complete(1, len(direct), "review")
        self.assertFalse(result["recovery_scheduled"])
        self.assertAlmostEqual(result["new_stability_days"], 4.4)
        before = self.stored(state).copy()
        FixedDateTime.current = NOW + datetime.timedelta(days=4.4)
        state = self.request("/api/state")
        task = self.task_for(state)
        self.assertEqual(task["task_type"], "review")
        self.assertIn("último repaso", task["reason"])
        # El repaso directo pendiente sobrevive a una tarea superior aprobada.
        higher, state = self.complete(4, 4, topic_id=DEPENDENT)
        self.assertNotIn(TOPIC, [boost["id"] for boost in higher["implicit_boosted"]])
        self.assertEqual(self.stored(state), before)

        retry = self.review_variant(TOPIC, "review", seed=13)
        result, state = self.complete(1, len(retry), "review")
        self.assertTrue(result["recovery_scheduled"])
        self.assertFalse(result["passed"])
        self.assertEqual(self.stored(state)["mastery"], 0.92)
        self.assertEqual(result["new_stability_days"], 1.0)
        self.assertIsNone(self.task_for(state))
        FixedDateTime.current += datetime.timedelta(days=1)
        state = self.request("/api/state")
        task = self.task_for(state)
        self.assertEqual(task["task_type"], "recovery")
        self.assertIn("2 repasos fallidos", task["reason"])

        guided = self.review_variant(TOPIC, "recovery", seed=14)
        result, state = self.complete(1, len(guided), "recovery")
        self.assertTrue(result["recovery_scheduled"])
        self.assertIsNone(self.task_for(state))
        FixedDateTime.current += datetime.timedelta(days=1)
        result, state = self.complete(3, len(guided), "recovery")
        self.assertTrue(result["passed"])
        self.assertEqual(result["implicit_boosted"], [])
        self.assertIsNone(self.task_for(state))
        FixedDateTime.current += datetime.timedelta(days=5)
        result, _ = self.complete(0, len(direct), "review")
        self.assertFalse(result["recovery_scheduled"])
        self.assertGreater(result["new_stability_days"], 1.0)

    def test_suspect_prerequisite_is_checked_directly_before_target_recovery(self):
        for mastery, due, reason in ((0.69, False, "bajo el 70 %"), (0.88, True, "está vencido")):
            with self.subTest(reason=reason):
                FixedDateTime.current = NOW
                self.prepare_review(mastery, due)
                self.complete(0, 3, "review")
                FixedDateTime.current += datetime.timedelta(days=4.4)
                _, state = self.complete(0, 3, "review")
                task = state["recommendations"][0]
                self.assertEqual(task["topic_id"], PREREQUISITE)
                self.assertEqual(task["task_type"], "prerequisite_check")
                self.assertIn(reason, task["reason"])
                self.assertIn("Límites", task["reason"])

                # Los respaldos previos ya contienen todo lo necesario para reconstruir la cola.
                snapshot = self.request("/api/backup")
                engine.import_backup_payload(snapshot)
                self.assertEqual(state["recommendations"], self.request("/api/state")["recommendations"])
                questions = self.review_variant(PREREQUISITE, "prerequisite_check", seed=15)
                self.assertTrue(all(question["is_parametric"] for question in questions))
                if due:
                    result, state = self.complete(2, len(questions), "prerequisite_check", topic_id=PREREQUISITE)
                    self.assertTrue(result["passed"])
                    self.assertEqual(result["implicit_boosted"], [])
                    self.assertIsNone(self.task_for(state, PREREQUISITE))
                    FixedDateTime.current += datetime.timedelta(days=1)
                    self.assertEqual(self.task_for(self.request("/api/state"))["task_type"], "recovery")
                    continue

                result, state = self.complete(0, len(questions), "prerequisite_check", topic_id=PREREQUISITE)
                self.assertFalse(result["passed"])
                self.assertEqual(self.stored(state, PREREQUISITE)["mastery"], mastery)
                self.assertEqual(self.task_for(state, PREREQUISITE)["task_type"], "recovery")
                self.assertIsNone(self.task_for(state))

                FixedDateTime.current += datetime.timedelta(days=1)
                self.assertIsNone(self.task_for(self.request("/api/state")))
                guided = self.review_variant(PREREQUISITE, "recovery", seed=16)
                result, state = self.complete(len(guided), len(guided), "recovery", topic_id=PREREQUISITE)
                self.assertTrue(result["passed"])
                self.assertEqual(result["implicit_boosted"], [])
                self.assertEqual(self.stored(state, PREREQUISITE)["mastery"], 1.0)
                self.assertEqual(self.task_for(state)["task_type"], "recovery")

    def test_pilot_lessons_replay_from_the_seed_without_changing_progress(self):
        before = self.request("/api/backup")
        for topic_id in ("ic_desigualdades", PREREQUISITE, TOPIC, DEPENDENT):
            with self.subTest(topic_id=topic_id):
                lesson = self.request(f"/api/topic/{topic_id}")
                rng_state = random.getstate()
                replay = engine.get_topic_lesson_payload(topic_id, seed=lesson["exercise_seed"])
                self.assertEqual(lesson, replay)
                self.assertEqual(rng_state, random.getstate())
                self.assertEqual(lesson["course_code"], "MAT1107")
                generated = [q for q in lesson["questions"] if q["is_parametric"]]
                self.assertEqual(len(generated), 2)
                self.assertNotEqual(generated[0]["prompt"], generated[1]["prompt"])
                if topic_id == PREREQUISITE:
                    self.assertIn("q_ic_fun_transferencia", [q["id"] for q in lesson["questions"]])
        self.assertEqual(before, self.request("/api/backup"))

    def test_direct_review_uses_distinct_prompts_when_a_family_repeats(self):
        questions = self.review_variant(DEPENDENT, "review", seed=14)
        self.assertEqual(len(questions), 3)
        self.assertEqual(len({question["prompt"] for question in questions}), 3)

    def test_three_zero_scores_do_not_unlock_but_passing_lesson_does(self):
        state = self.request("/api/state")
        self.assertEqual(self.topic(state, DEPENDENT)["status"], "locked")
        original = self.stored(state).copy()
        rng_state = random.getstate()
        self.addCleanup(random.setstate, rng_state)
        random.seed(1107)
        lesson = self.request(f"/api/topic/{TOPIC}")
        mastery_history = []

        for attempt in range(1, 4):
            with self.subTest(attempt=attempt):
                result, state = self.complete(0, 4, snapshot=state["backup_snapshot"])
                mastery_history.append(self.stored(state)["mastery"])
                self.assertFalse(result["passed"])
                self.assertFalse(result["review_scheduled"])
                self.assertEqual(result["new_mastery"], 0)
                self.assertEqual(self.stored(state), {**original, "total_attempts": 4 * attempt})
                self.assertEqual(self.topic(state, DEPENDENT)["status"], "locked")
                log = state["backup_snapshot"]["xp_log"][-1]
                self.assertEqual(log["score_ratio"], 0)
                self.assertGreater(log["xp_earned"], 0)

        self.assertEqual(mastery_history, [0, 0, 0])
        total = len(lesson["questions"])
        result, state = self.complete(total, total)
        self.assertTrue(result["passed"])
        self.assertTrue(result["review_scheduled"])
        self.assertEqual(result["score_ratio"], 1.0)
        self.assertEqual(self.stored(state)["mastery"], 1.0)
        self.assertEqual(self.topic(state, DEPENDENT)["status"], "available")

    def test_threshold_uses_unrounded_score_and_failed_review_cannot_create_mastery(self):
        state = self.request("/api/state")
        snapshot = state["backup_snapshot"]
        self.stored(state).update(mastery=0.69)
        self.stored(state, PREREQUISITE).update(mastery=0.88)
        engine.import_backup_payload(snapshot)
        original_prerequisite = self.stored(state, PREREQUISITE)

        result, state = self.complete(649, 1000, task_type="review")
        self.assertFalse(result["passed"])
        self.assertEqual(result["score_ratio"], 0.649)
        self.assertEqual(self.stored(state)["mastery"], 0.69)
        self.assertEqual(self.stored(state, PREREQUISITE), original_prerequisite)
        self.assertEqual(result["implicit_boosted"], [])
        self.assertEqual(self.topic(state, DEPENDENT)["status"], "locked")

        result, state = self.complete(650, 1000)
        self.assertTrue(result["passed"])
        self.assertEqual(result["score_ratio"], 0.65)
        self.assertAlmostEqual(self.stored(state)["mastery"], 0.9125)
        self.assertEqual(result["implicit_boosted"], [])
        self.assertEqual(self.stored(state, PREREQUISITE), original_prerequisite)

    def test_failed_review_preserves_history_and_is_due_before_passing_review(self):
        self.complete(4, 4)
        initial = self.request("/api/state")
        original = self.stored(initial)
        original.update(
            mastery=0.92,
            stability_days=8.0,
            repetitions=3,
            last_practiced_ts=NOW.timestamp() - 8 * DAY,
            next_review_ts=NOW.timestamp(),
        )
        snapshot = initial["backup_snapshot"]
        engine.import_backup_payload(snapshot)

        fail, failed_state = self.complete(2, 4, task_type="review")
        engine.import_backup_payload(snapshot)
        success, passed_state = self.complete(4, 4, task_type="review")
        failed = self.stored(failed_state)
        passed = self.stored(passed_state)

        self.assertFalse(fail["passed"])
        self.assertTrue(success["passed"])
        self.assertTrue(fail["review_scheduled"])
        self.assertEqual(failed["mastery"], original["mastery"])
        self.assertEqual(failed["repetitions"], original["repetitions"] + 1)
        self.assertEqual(failed["total_attempts"], original["total_attempts"] + 4)
        self.assertEqual(failed["correct_attempts"], original["correct_attempts"] + 2)
        self.assertEqual(failed["last_practiced_ts"], NOW.timestamp())
        self.assertEqual(passed["last_practiced_ts"], NOW.timestamp())
        self.assertAlmostEqual((failed["next_review_ts"] - NOW.timestamp()) / DAY, 4.4)
        self.assertAlmostEqual((passed["next_review_ts"] - NOW.timestamp()) / DAY, 21.6)
        self.assertEqual(self.topic(failed_state, DEPENDENT)["status"], "available")

        log = failed_state["backup_snapshot"]["xp_log"]
        # La importación recrea las filas y reasigna sus IDs.
        for saved, restored in zip(snapshot["xp_log"], log[:-1], strict=True):
            self.assertEqual({**saved, "id": restored["id"]}, restored)
        self.assertEqual(log[-1]["task_type"], "review")
        self.assertEqual(log[-1]["score_ratio"], 0.5)
        self.assertEqual(failed_state["profile"]["total_xp"], initial["profile"]["total_xp"] + fail["xp_earned"])

        FixedDateTime.current = NOW + datetime.timedelta(days=5)
        engine.import_backup_payload(failed_state["backup_snapshot"])
        state = self.request("/api/state")
        self.assertEqual(self.topic(state, TOPIC)["status"], "review_due")
        engine.import_backup_payload(passed_state["backup_snapshot"])
        state = self.request("/api/state")
        self.assertEqual(self.topic(state, TOPIC)["status"], "mastered")
