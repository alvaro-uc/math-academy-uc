import datetime
import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import diagnostic
import engine
from test_mastery import DAY, DEPENDENT, NOW, PREREQUISITE, TOPIC, FixedDateTime, LearningAPITestCase


FOUNDATION = "ic_desigualdades"
PATH = "/api/diagnostic"
SEED = 1107


class DiagnosticTests(LearningAPITestCase):
    def start(self, **payload):
        with patch.object(engine.random, "getrandbits", return_value=SEED):
            return self.request(PATH, {"start": True, **payload})

    def answer_payload(self, response, correct):
        session = response["diagnostic"]
        snapshot = response["state"]["backup_snapshot"]
        restored = diagnostic.restore_session(snapshot["diagnostic"]["session"])
        self.assertEqual(session, diagnostic.public_session(restored))
        question = restored["current"]["question"]
        index = question["correct_index"]
        choice = None if correct is None else index if correct else (index + 1) % len(question["options"])
        return {
            "session_id": session["session_id"], "answered": session["answered"],
            "choice": choice, "client_backup": snapshot,
        }

    def answer(self, response, correct):
        return self.request(PATH, self.answer_payload(response, correct))

    def rows(self, response):
        return {row["topic_id"]: row for row in response["state"]["backup_snapshot"]["topic_state"]}

    def evidence(self, response):
        return {row["topic_id"]: row for row in response["diagnostic"]["evidence"]}

    def assert_item(self, response, topic, reason):
        session = response["diagnostic"]
        self.assertEqual(session["status"], "in_progress")
        self.assertEqual(session["item"]["topic_id"], topic)
        self.assertEqual(session["item"]["reason"], reason)
        self.assertEqual(set(session["item"]["question"]), {"prompt", "options"})

    def test_two_profiles_branch_and_only_direct_success_updates_mastery(self):
        weak = self.start()
        self.assert_item(weak, PREREQUISITE, "initial")
        weak = self.answer(weak, False)
        self.assert_item(weak, FOUNDATION, "prerequisite")
        weak = self.answer(weak, False)
        self.assertEqual(weak["diagnostic"]["answered"], 2)
        self.assertEqual(self.evidence(weak)[FOUNDATION]["kind"], "direct")
        self.assertEqual(self.evidence(weak)[TOPIC]["kind"], "inferred")
        self.assertIn(PREREQUISITE, self.evidence(weak)[TOPIC]["negative_from"])
        self.assertTrue(all(row["mastery"] == 0 for row in self.rows(weak).values()))

        strong = self.start(restart_from=weak["diagnostic"]["session_id"])
        self.assertNotEqual(strong["diagnostic"]["session_id"], weak["diagnostic"]["session_id"])
        for topic, reason in (
            (PREREQUISITE, "initial"), (TOPIC, "successor"),
            (DEPENDENT, "successor"), (FOUNDATION, "confirm_inference"),
        ):
            self.assert_item(strong, topic, reason)
            self.assertEqual(self.rows(strong)[FOUNDATION]["mastery"], 0)
            strong = self.answer(strong, True)
        self.assertEqual(strong["diagnostic"]["answered"], 4)
        self.assertEqual(strong["diagnostic"]["status"], "completed")
        for topic in (FOUNDATION, PREREQUISITE, TOPIC, DEPENDENT):
            row = self.rows(strong)[topic]
            self.assertEqual(row["mastery"], 0.75)
            self.assertEqual(row["next_review_ts"], NOW.timestamp() + 2 * DAY)
            self.assertEqual(self.evidence(strong)[topic]["correct"], 1)
        self.assertEqual(strong["state"]["profile"]["total_xp"], 0)
        self.assertEqual(strong["state"]["backup_snapshot"]["xp_log"], [])
        self.assertEqual(strong["state"]["profile"]["diagnostic_completed"], 1)

    def test_contradictory_inference_triggers_a_different_family(self):
        response = self.start()
        for _ in range(3):
            response = self.answer(response, True)
        self.assert_item(response, FOUNDATION, "confirm_inference")
        first = response["diagnostic"]["item"]["question"]
        response = self.answer(response, False)
        self.assert_item(response, FOUNDATION, "resolve_conflict")
        self.assertNotEqual(first["prompt"], response["diagnostic"]["item"]["question"]["prompt"])
        response = self.answer(response, True)
        self.assertEqual(response["diagnostic"]["answered"], 5)
        row = self.evidence(response)[FOUNDATION]
        self.assertEqual((row["kind"], row["correct"], row["incorrect"]), ("direct", 1, 1))
        self.assertIn(PREREQUISITE, row["positive_from"])
        self.assertEqual(self.rows(response)[FOUNDATION]["mastery"], 0)
        self.assertIsNone(self.rows(response)[FOUNDATION]["next_review_ts"])

    def test_interruption_backup_and_duplicate_submissions(self):
        first = self.start()
        stale = first["state"]["backup_snapshot"]
        bad = {**self.answer_payload(first, True), "choice": True}
        self.request(PATH, bad, status="400 Bad Request")
        self.assertEqual(self.request(PATH), first["diagnostic"])

        second = self.answer(first, False)
        question = second["diagnostic"]
        FixedDateTime.current = NOW + datetime.timedelta(days=3)
        self.request("/api/state", {"client_backup": stale})
        self.assertEqual(self.request(PATH), question)
        self.assertEqual(self.answer(first, True)["diagnostic"], question)

        exported = self.request("/api/backup")
        with patch.object(engine, "DB_PATH", os.path.join(os.path.dirname(engine.DB_PATH), "restored.db")):
            self.request("/api/backup", exported)
            self.assertEqual(self.request(PATH), question)
            payload = self.answer_payload(second, True)
            with ThreadPoolExecutor(max_workers=2) as pool:
                first_result, duplicate = list(pool.map(lambda _: self.request(PATH, payload), range(2)))
            self.assertEqual(first_result["diagnostic"], duplicate["diagnostic"])
            self.assertEqual(first_result["diagnostic"]["answered"], 2)
            row = self.rows(duplicate)[FOUNDATION]
            self.assertEqual(row["repetitions"], 1)
            self.assertEqual(row["next_review_ts"], NOW.timestamp() + 5 * DAY)
            self.assertEqual(duplicate["state"]["profile"]["total_xp"], 0)

    def test_clean_start_demo_omissions_and_legacy_backup(self):
        clean = self.request("/api/state")
        self.assertIsNone(clean["preset_mode"])
        self.assertEqual(clean["profile"]["total_xp"], 0)
        self.assertEqual(clean["profile"]["diagnostic_completed"], 0)
        self.assertTrue(all(row["mastery"] == 0 for row in clean["backup_snapshot"]["topic_state"]))
        self.assertEqual(self.request(PATH)["status"], "idle")

        demo = self.request("/api/profile", {"preset_mode": "mid_sem1"})["state"]
        self.assertEqual(demo["preset_mode"], "mid_sem1")
        self.assertEqual(demo["profile"]["total_xp"], 45)
        self.assertEqual(demo["profile"]["diagnostic_completed"], 0)
        self.assertEqual(self.request(PATH)["status"], "idle")
        response = self.answer(self.answer(self.start(), None), None)
        self.assertTrue(all(row["kind"] == "unassessed" for row in self.evidence(response).values()))
        self.assertEqual(response["state"]["profile"]["total_xp"], 45)
        self.assertEqual(self.rows(response)[PREREQUISITE]["mastery"], 0.88)

        legacy = {key: value for key, value in demo["backup_snapshot"].items() if key != "diagnostic"}
        restored = self.request("/api/backup", legacy)["state"]
        self.assertIsNone(restored["preset_mode"])
        self.assertEqual(restored["backup_snapshot"]["topic_state"], legacy["topic_state"])
        self.assertEqual(self.request(PATH)["status"], "idle")

        reset = self.request("/api/profile", {"preset_mode": "reset"})["state"]
        self.assertIsNone(reset["preset_mode"])
        self.assertEqual(reset["profile"]["total_xp"], 0)
        self.assertEqual(reset["profile"]["diagnostic_completed"], 0)
        self.assertEqual(reset["diagnostic"], "idle")
