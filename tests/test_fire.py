import datetime
import json
import os
import random
import re
from fractions import Fraction
from unittest.mock import patch

import engine
import fire
from generators import gen_continuous_radical_extension
from test_mastery import DAY, DEPENDENT, NOW, PREREQUISITE, TOPIC, FixedDateTime, LearningAPITestCase


FOUNDATION = "ic_desigualdades"
PATH = "/api/study"


class FireTests(LearningAPITestCase):
    def prepare(self):
        snapshot = self.request("/api/backup")
        for row in snapshot["topic_state"]:
            if row["topic_id"] in (FOUNDATION, PREREQUISITE, TOPIC, DEPENDENT):
                row.update(
                    mastery=0.92, stability_days=8.0, repetitions=3,
                    last_practiced_ts=NOW.timestamp() - 8 * DAY, next_review_ts=NOW.timestamp(),
                )
        engine.import_backup_payload(snapshot)
        return snapshot

    def stored(self, snapshot, topic_id=FOUNDATION):
        return next(row for row in snapshot["topic_state"] if row["topic_id"] == topic_id)

    def review(self, topic_id, seed, is_correct, seconds=0, task_type="review"):
        started = FixedDateTime.current
        with patch.object(engine.random, "getrandbits", return_value=seed):
            session = self.request(PATH, {
                "kind": "lesson", "action": "open", "topic_id": topic_id, "task_type": task_type,
            })["session"]
        self.assertEqual(session["step"], 1)
        questions = session["topic"]["questions"]
        for index, question in enumerate(questions):
            payload = {
                "kind": "lesson", "action": "advance", "slot": session["slot"], "session_id": session["id"],
                "step": index + 1, "answered": index,
            }
            correct = question["correct_index"]
            choice = correct if is_correct(index, question) else (correct + 1) % len(question["options"])
            FixedDateTime.current = started + datetime.timedelta(seconds=seconds * (index + 1) / len(questions))
            self.request(PATH, {**payload, "choice": choice})
            final = {**payload, "answered": index + 1}
            response = self.request(PATH, final)
        return questions, response, final

    def due(self, state, topic_id=FOUNDATION):
        return next(t["due_for_review"] for t in state["topics"] if t["id"] == topic_id)

    def test_matched_trace_direct_control_and_fire_with_delayed_probes(self):
        baseline = self.prepare()
        before = self.request("/api/state")
        self.assertTrue(any(task["topic_id"] == FOUNDATION for task in before["recommendations"]))
        outcomes = {}
        for enabled in ("0", "1"):
            FixedDateTime.current = NOW
            engine.import_backup_payload(baseline)
            with patch.dict(os.environ, FIRE_ENABLED=enabled):
                questions, advanced, final = self.review(
                    DEPENDENT, 1107, lambda _, q: q.get("fire_audit") != "derivada_por_definicion",
                )
                state = advanced["state"]
                result = advanced["session"]["result"]
                self.assertEqual(result["score_ratio"], 2 / 3)
                self.assertEqual(self.request(PATH, final)["session"]["result"], result)
                self.assertEqual(len(self.request("/api/backup")["xp_log"]), 1)
                row = self.stored(state["backup_snapshot"])
                if enabled == "1":
                    credit = [item for item in result["implicit_boosted"] if item["id"] == FOUNDATION]
                    self.assertEqual(len(credit), 1)
                    self.assertAlmostEqual(credit[0]["weight"], 0.45 / 3)
                    self.assertEqual(credit[0]["postponed_days"], 1.2)
                    self.assertEqual(len(credit[0]["evidence"]), 1)
                    self.assertEqual(credit[0]["evidence"][0]["path"], [DEPENDENT, PREREQUISITE, FOUNDATION])
                    self.assertAlmostEqual(row["next_review_ts"], NOW.timestamp() + 1.2 * DAY)
                    original = self.stored(baseline)
                    self.assertEqual(row, {**original, "stability_days": 9.2, "next_review_ts": row["next_review_ts"]})
                    self.assertFalse(self.due(state))
                    log = state["backup_snapshot"]["xp_log"][0]
                    self.assertEqual(json.loads(log["implicit_topics_json"]), result["implicit_boosted"])
                else:
                    self.assertEqual(result["implicit_boosted"], [])
                    self.assertEqual(row, self.stored(baseline))
                    self.assertTrue(self.due(state))

                # La única práctica adicional del control es el repaso que sigue vencido.
                started = FixedDateTime.current
                if self.due(state):
                    _, direct, _ = self.review(FOUNDATION, 31, lambda *_: True, seconds=210)
                    self.assertEqual(self.stored(direct["state"]["backup_snapshot"])["repetitions"], 4)
                    self.assertEqual(direct["session"]["result"]["new_stability_days"], 21.6)
                direct_seconds = (FixedDateTime.current - started).total_seconds()
                after_policy = self.request("/api/backup")

                probes = []
                seen = {q["prompt"] for q in engine.get_topic_lesson_payload(
                    FOUNDATION, seed=31, task_type="review",
                )["questions"]}
                # Ramas independientes para que la prueba del día 7 no entrene para el día 14.
                for day, seed, hits in ((7, 123, 3), (14, 567, 2)):
                    FixedDateTime.current = NOW + datetime.timedelta(days=day)
                    engine.import_backup_payload(after_policy)
                    self.assertEqual(self.due(self.request("/api/state")), enabled == "1")
                    variants, probe, _ = self.review(FOUNDATION, seed, lambda index, _: index < hits)
                    prompts = {q["prompt"] for q in variants}
                    self.assertFalse(prompts & seen)
                    seen.update(prompts)
                    probes.append((variants, probe["session"]["result"]["score_ratio"]))
                outcomes[enabled] = (questions, probes, direct_seconds)

        self.assertEqual(outcomes["0"][:2], outcomes["1"][:2])
        self.assertEqual([score for _, score in outcomes["1"][1]], [1, 2 / 3])
        self.assertEqual((outcomes["0"][2], outcomes["1"][2]), (210, 0))

    def test_only_approved_audited_answers_can_move_a_review(self):
        baseline = self.prepare()
        cases = (
            (lambda _, q: q.get("fire_audit") == "extension_radical", "review", set()),
            (lambda _, q: q.get("fire_audit") != "extension_radical", "review", {TOPIC}),
            (lambda *_: True, "prerequisite_check", set()),
        )
        for answers, task_type, targets in cases:
            with self.subTest(task_type=task_type, targets=targets):
                engine.import_backup_payload(baseline)
                _, response, _ = self.review(DEPENDENT, 1107, answers, task_type=task_type)
                result = response["session"]["result"]
                self.assertEqual({item["id"] for item in result["implicit_boosted"]}, targets)
                self.assertEqual(self.stored(response["state"]["backup_snapshot"]), self.stored(baseline))

        # Un error previo exige evidencia directa aunque la pregunta superior se acierte.
        engine.import_backup_payload(baseline)
        self.review(FOUNDATION, 31, lambda *_: False)
        before = self.stored(self.request("/api/backup"))
        FixedDateTime.current = NOW + datetime.timedelta(days=4.4)
        _, response, _ = self.review(DEPENDENT, 1107, lambda *_: True)
        self.assertTrue(self.due(response["state"]))
        self.assertEqual(self.stored(response["state"]["backup_snapshot"]), before)

    def test_radical_variants_and_converging_evidence(self):
        prompts = set()
        for seed in range(128):
            question = gen_continuous_radical_extension(rng=random.Random(seed))
            prompts.add(question["prompt"])
            a, linear, constant = map(int, re.search(
                r"Para \$x\\ne (\d+).*x\^2-(\d+)x\+(\d+)", question["prompt"],
            ).groups())
            b = linear - a
            self.assertEqual(a * b, constant)
            self.assertGreater(a, b)
            answer = question["options"][question["correct_index"]]
            endpoint, excluded, point, root = map(int, re.findall(r"\d+", answer))
            self.assertEqual((endpoint, excluded, point), (b, a, a))
            self.assertEqual(root**2, a - b)
            for x, in_domain in ((b - 1, False), (b, True), (a - 1, True), (a + 1, True)):
                self.assertEqual(Fraction(x**2 - linear * x + constant, x - a) >= 0, in_domain)
            self.assertEqual(len(set(question["options"])), 4)
        self.assertGreater(len(prompts), 20)

        audit = fire.question_evidence(DEPENDENT, question)
        self.assertAlmostEqual(audit[FOUNDATION]["weight"], 0.45)
        self.assertEqual(audit[FOUNDATION]["path"], [DEPENDENT, PREREQUISITE, FOUNDATION])
        with patch.dict(fire.AUDITS, {"extension_radical": (DEPENDENT, {
            DEPENDENT: {TOPIC: (0.60, "límite")},
            TOPIC: {FOUNDATION: (0.50, "signo")},
        })}):
            self.assertAlmostEqual(fire.question_evidence(DEPENDENT, question)[FOUNDATION]["weight"], 0.30)
        correct = question["correct_index"]
        duplicates = fire.review_evidence(DEPENDENT, [question, question], [correct, correct])
        self.assertEqual(duplicates[FOUNDATION], [audit[FOUNDATION]])

    def test_early_credit_is_discounted_and_unlearned_topics_are_excluded(self):
        row = self.stored(self.prepare())
        self.assertIsNone(fire.extended_schedule(row, 0.15, row["last_practiced_ts"]))
        self.assertIsNone(fire.extended_schedule({**row, "mastery": 0.70}, 0.15, NOW.timestamp()))
        self.assertIsNone(fire.extended_schedule({**row, "repetitions": 0}, 0.15, NOW.timestamp()))
        _, _, days = fire.extended_schedule(row, 0.15, NOW.timestamp() - 4 * DAY)
        self.assertAlmostEqual(days, 0.60)
        _, deadline, days = fire.extended_schedule(row, 0.15, NOW.timestamp() + 2 * DAY)
        self.assertAlmostEqual(days, 1.20)
        self.assertLess(deadline, NOW.timestamp() + 2 * DAY)
