import math
import random
import re
import unittest
from fractions import Fraction

from curriculum import TOPICS
from generators import GENERATORS, PILOT_FAMILY_COUNTS


def selected_answer(question):
    return question["options"][question["correct_index"]]


def numbers(text):
    return [int(value.replace(" ", "")) for value in re.findall(r"-? *\d+", text)]


def exact_number(option):
    body = option.strip("$")
    if body.startswith(r"\frac"):
        return Fraction(*numbers(body))
    return Fraction(body)


class PilotExercisesTests(unittest.TestCase):
    def check_inequality(self, variant, question):
        prompt = question["prompt"]
        answer = selected_answer(question)
        if variant < 2:
            left, right = numbers(answer)
            if variant == 0:
                coefficient, *offset, bound = numbers(prompt)
                constant = offset[0] if offset else 0
                self.assertEqual(coefficient * left + constant, -bound)
                self.assertEqual(coefficient * right + constant, bound)
                self.assertEqual((answer[1], answer[-2]), ("(", ")"))
            else:
                numerator_root = -numbers(prompt)[0]
                denominator_offset = numbers(prompt)[1:-1]
                self.assertEqual(left, -(denominator_offset[0] if denominator_offset else 0))
                self.assertEqual(right, numerator_root)
                self.assertEqual((answer[1], answer[-2]), ("(", "]"))
            self.assertLess(left, right)
        elif variant == 2:
            center, offset, _ = numbers(prompt)
            infimum, supremum = numbers(answer)
            self.assertEqual(infimum, center - offset)
            self.assertEqual(supremum, center)
            self.assertLess(infimum, supremum)
        else:
            _, offset, _, _, _, numerator, denominator = numbers(prompt)
            n = int(exact_number(answer))
            tolerance = Fraction(numerator, denominator)
            self.assertGreater(n, 1)
            self.assertLess(Fraction(offset, n), tolerance)
            self.assertGreaterEqual(Fraction(offset, n - 1), tolerance)

    def check_functions(self, variant, question):
        answer = selected_answer(question)
        if variant == 0:
            a, b, _, minus_c, x, _ = numbers(question["prompt"])
            self.assertEqual(exact_number(answer), (a * x + b)**2 + minus_c)
        elif variant == 1:
            a, b, _, y = numbers(question["prompt"])
            self.assertEqual(a * exact_number(answer) + b, y)
        else:
            _, b, c, endpoint = numbers(question["prompt"])
            self.assertEqual(2 * endpoint + b, 0)
            self.assertEqual(numbers(answer), [endpoint**2 + b * endpoint + c])
            self.assertTrue(answer.startswith("$["))

    def check_limits(self, variant, question):
        answer = exact_number(selected_answer(question))
        prompt = question["prompt"]
        if variant == 0:
            point = numbers(prompt)[0]
            polynomial = re.search(r"\\frac\{x\^2([^}]*)\}", prompt)[1].replace(" ", "")
            linear, separator, constant = polynomial.partition("x")
            b = int(linear) if separator else 0
            constant = constant if separator else linear
            c = int(constant or 0)
            self.assertEqual(point**2 + b * point + c, 0)
            for dx in (Fraction(-1, 10), Fraction(1, 10)):
                x = point + dx
                self.assertEqual((x**2 + b * x + c) / dx - dx, answer)
        elif variant == 1:
            _, square, coefficient, minus_root = numbers(prompt)
            self.assertGreater(square, 0)
            self.assertEqual(square, minus_root**2)
            self.assertEqual(answer * (-2 * minus_root), coefficient)
            for dx in (-0.001, 0.001):
                self.assertGreater(square + coefficient * dx, 0)
                original = (math.sqrt(square + coefficient * dx) + minus_root) / dx
                self.assertAlmostEqual(original, float(answer), delta=0.002)
        else:
            _, p, q = numbers(prompt)
            self.assertNotEqual(q, 0)
            self.assertEqual(answer * q, p)
            for dx in (-0.001, 0.001):
                self.assertAlmostEqual(math.sin(p * dx) / (q * dx), float(answer), delta=0.001)

    def check_continuity(self, variant, question):
        prompt = question["prompt"]
        answer = selected_answer(question)
        if variant == 0:
            _, c, point, _, _ = numbers(prompt)
            a, b = numbers(answer)
            self.assertEqual(a * point + b, point**2 + c)
            dx = Fraction(-1, 10)
            left_secant = ((point + dx)**2 + c - (point**2 + c)) / dx
            self.assertEqual(left_secant - dx, a)
        else:
            _, minus_a, c, _, point = numbers(prompt)
            f_at_point = point**3 + minus_a * point + c
            # El promedio de dos pendientes secantes simétricas cancela el término lineal en h.
            slopes = []
            for dx in (Fraction(-1, 10), Fraction(1, 10)):
                x = point + dx
                slopes.append((x**3 + minus_a * x + c - f_at_point) / dx)
            self.assertEqual(sum(slopes) / 2 - dx**2, exact_number(answer))

    def test_parametric_families_across_128_seeds(self):
        checks = {
            "inequality_abs": self.check_inequality,
            "function_composition": self.check_functions,
            "limit_rational": self.check_limits,
            "continuity_param": self.check_continuity,
        }
        for generator, family_count in PILOT_FAMILY_COUNTS.items():
            for variant in range(family_count):
                for seed in range(128):
                    with self.subTest(generator=generator, variant=variant, seed=seed):
                        question = GENERATORS[generator](variant, rng=random.Random(seed))
                        self.assertEqual(len(set(question["options"])), 4)
                        self.assertIn("Error típico", question["explanation"])
                        self.assertTrue(question["hint"])
                        checks[generator](variant, question)

    def test_known_transfer_problem_has_the_expected_endpoints(self):
        topic = next(item for item in TOPICS if item["id"] == "ic_funciones")
        question = next(
            item for item in topic["questions"]
            if item["id"] == "q_ic_fun_transferencia"
        )
        self.assertEqual(selected_answer(question), "$[5,6)$")
        for time, expected in [(4.5, False), (5, True), (5.5, True), (6, False), (9, False)]:
            with self.subTest(time=time):
                self.assertEqual(5 <= time <= 9 and -(time**2 - 10 * time + 24) > 0, expected)

    def test_known_exact_answers(self):
        cases = [
            ("inequality_abs", 1, r"$(-3,\; 5]$"),
            ("inequality_abs", 3, "$25$"),
            ("function_composition", 0, "$97$"),
            ("limit_rational", 1, r"$\frac{2}{3}$"),
            ("continuity_param", 0, r"$a = 6,\; b = -7$"),
        ]
        for generator, variant, expected in cases:
            with self.subTest(generator=generator, variant=variant):
                question = GENERATORS[generator](variant, rng=random.Random(1107))
                self.assertEqual(selected_answer(question), expected)
