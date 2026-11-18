from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import general
from test_mastery import LearningAPITestCase, NOW, TOPIC


class GeneralRouteTests(LearningAPITestCase):
    def test_existing_seven_correct_count_toward_goal_and_recent_activity(self):
        skill = "arithmetic.multiply-by-digit"
        now = NOW.timestamp()
        with general.database() as cur:
            for number in range(1, 8):
                when = now - 9 * 86400 if number == 1 else now
                answer = general.exercise(skill, number)[1]
                cur.execute("INSERT INTO general_attempt VALUES (?, ?, ?, 1, ?)", (skill, number, answer, when))
        with patch.object(general.time, "time", return_value=now):
            data = self.request("/api/general")
            self.assertEqual(data[skill]["correct"], data["_summary"]["goal"])
            self.assertEqual(len(data["_summary"]["recent"]), 6)
            self.assertEqual(data["algebra.linear-equation"]["correct"], 0)

    def test_route_switch_preserves_uc_and_each_first_attempt(self):
        self.request("/api/study", {"kind": "lesson", "action": "open", "topic_id": TOPIC, "task_type": "lesson"})
        uc = self.request("/api/backup")
        first = self.request("/api/general")
        self.assertEqual(first, self.request("/api/general"))
        with patch.object(general.time, "time", return_value=NOW.timestamp()):
            for skill in general.SKILLS:
                prompt, expected, _ = general.exercise(skill, 1)
                self.assertEqual(first[skill]["prompt"], prompt)
                body = {"skill": skill, "number": 1, "answer": expected}
                self.request("/api/general", {**body, "number": 2}, status="400 Bad Request")
                with ThreadPoolExecutor(2) as pool:
                    results = list(pool.map(lambda _: self.request("/api/general", body), range(2)))
                self.assertTrue(results[0]["correct"])
                self.assertEqual(results[0], results[1])
                self.assertEqual(results[0], self.request("/api/general", {**body, "answer": expected + 1}))
                self.assertEqual(self.request("/api/general")[skill]["correct"], 1)
                self.assertEqual(self.request("/api/general")[skill]["number"], 2)
        after = self.request("/api/backup")
        for key in ("topic_state", "study", "xp_log", "profile"):
            self.assertEqual(uc[key], after[key])
        self.request("/api/backup", uc)
        self.assertEqual(self.request("/api/general")[skill]["number"], 2)

    def test_general_requires_login(self):
        self.token = ""
        self.request("/api/general", status="401 Unauthorized")
        self.request("/api/general", {}, status="401 Unauthorized")
