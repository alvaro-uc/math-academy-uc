"""Práctica local de la ruta general. Los identificadores describen habilidades."""
import random
import time
from contextlib import closing, contextmanager

import engine


def multiplication(rng):
    a, b = rng.randint(12, 89), rng.randint(3, 9)
    return (f"Calcula {a} × {b}.", a * b,
            f"Separa {a} en decenas y unidades. Multiplica cada parte por {b} y suma los productos.")


def equation(rng):
    a, b, x = rng.randint(2, 9), rng.randint(1, 16), rng.randint(-8, 12)
    c = a * x + b
    return (f"¿Qué valor de x cumple {a}x + {b} = {c}?", x,
            f"Resta {b} en ambos lados. Luego divide {c - b} por {a}.")


def derivative(rng):
    a, b, x = rng.randint(2, 8), rng.randint(1, 12), rng.randint(-5, 7)
    return (f"Si f(x) = {a}x² + {b}x, ¿cuánto vale f′({x})?", 2 * a * x + b,
            f"La regla de la potencia da f′(x) = {2*a}x + {b}. Evalúa en x = {x}.")


SKILLS = {
    "arithmetic.multiply-by-digit": ("Multiplicar por una cifra", "Por ejemplo, 23 × 4 = 20 × 4 + 3 × 4 = 92.", multiplication),
    "algebra.linear-equation": ("Resolver una ecuación lineal", "En 3x + 2 = 14, restamos 2 y dividimos por 3 para obtener x = 4.", equation),
    "calculus.quadratic-slope": ("Calcular la pendiente en un punto", "Para f(x) = 3x² + x, la derivada es 6x + 1. En x = 2, la pendiente vale 13.", derivative),
}


def exercise(skill, number):
    return SKILLS[skill][2](random.Random(f"general.v1/{skill}/{number}"))


@contextmanager
def database():
    with closing(engine.get_conn()) as conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS general_attempt (
            skill TEXT NOT NULL, number INTEGER NOT NULL, answer BIGINT NOT NULL,
            correct INTEGER NOT NULL, created_ts DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (skill, number))""")
        yield cur
        conn.commit()


def overview():
    with database() as cur:
        cur.execute("SELECT skill, COUNT(*) AS attempts, SUM(correct) AS correct FROM general_attempt GROUP BY skill")
        counts = {row["skill"]: row for row in cur.fetchall()}
    result = {}
    for skill, (title, example, _) in SKILLS.items():
        row = counts.get(skill, {"attempts": 0, "correct": 0})
        number = row["attempts"] + 1
        result[skill] = dict(title=title, example=example, number=number,
                             correct=row["correct"], prompt=exercise(skill, number)[0])
    return result


def answer(body):
    if not isinstance(body, dict):
        raise ValueError("Respuesta inválida.")
    skill, number, value = (body.get(key) for key in ("skill", "number", "answer"))
    if (not isinstance(skill, str) or skill not in SKILLS or type(number) is not int
            or not 1 <= number < 2**31 or type(value) is not int or abs(value) >= 2**53):
        raise ValueError("Se requiere una habilidad, un ejercicio y una respuesta entera.")
    _, expected, explanation = exercise(skill, number)
    with database() as cur:
        cur.execute("""INSERT INTO general_attempt (skill, number, answer, correct, created_ts)
                       SELECT ?, ?, ?, ?, ? WHERE ? = 1 OR EXISTS
                         (SELECT 1 FROM general_attempt WHERE skill = ? AND number = ?)
                       ON CONFLICT (skill, number) DO NOTHING""",
                    (skill, number, value, int(value == expected), time.time(), number, skill, number - 1))
        cur.execute("SELECT answer, correct FROM general_attempt WHERE skill = ? AND number = ?", (skill, number))
        saved = cur.fetchone()
    if saved is None:
        raise ValueError("Actualiza la práctica para continuar con el ejercicio pendiente.")
    return dict(answer=saved["answer"], correct=bool(saved["correct"]), expected=expected, explanation=explanation)
