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


class MasteryTests(unittest.TestCase):
    def setUp(self):
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch.dict(os.environ, {"APP_PASSWORD": "clave de prueba"}, clear=True))
        self.enterContext(patch.object(engine, "DB_PATH", os.path.join(tmp, "test.db")))
        self.enterContext(patch.object(engine.datetime, "datetime", FixedDateTime))
        self.enterContext(patch.object(engine.datetime, "date", FixedDate))
        self.enterContext(patch.object(FixedDateTime, "current", NOW))
        login = self.request("/api/auth/login", {"password": "clave de prueba"})
        self.token = login["token"]

    def request(self, path, payload=None):
        environ = {}
        setup_testing_defaults(environ)
        environ["PATH_INFO"] = path
        environ["HTTP_AUTHORIZATION"] = f"Bearer {getattr(self, 'token', '')}"
        if payload is not None:
            body = json.dumps(payload).encode()
            environ.update(REQUEST_METHOD="POST", CONTENT_LENGTH=str(len(body)))
            environ["wsgi.input"] = io.BytesIO(body)
        statuses = []
        response = app.application(environ, lambda status, headers: statuses.append(status))
        self.assertEqual(statuses, ["200 OK"], response)
        return json.loads(b"".join(response))

    def complete(self, correct, total, task_type="lesson", snapshot=None):
        response = self.request(
            "/api/complete",
            {
                "topic_id": TOPIC,
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
        self.assertTrue(result["implicit_boosted"])

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
