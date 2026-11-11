# -*- coding: utf-8 -*-
"""
Generador Paramétrico de Problemas Matemáticos (Estilo Math Academy)
Genera ejercicios dinámicos con parámetros aleatorios, distractores plausibles
que capturan errores comunes de Interrogación UC, y solución paso a paso en LaTeX.
"""

import math
import random
import uuid
from fractions import Fraction


def _make_mcq(prompt, correct_str, wrong_strs, hint, explanation, *, rng=None):
    """Empaqueta una pregunta MCQ barajando las opciones sin duplicados."""
    if rng is not None:
        options = [correct_str, *wrong_strs]
        if len(options) != 4 or len(set(options)) != 4:
            raise ValueError("La variante debe tener cuatro alternativas distintas")
        rng.shuffle(options)
        question_id = f"gen_{rng.getrandbits(64):016x}"
    else:
        options = _legacy_options(correct_str, wrong_strs)
        question_id = "gen_" + uuid.uuid4().hex[:8]
    return {
        "id": question_id,
        "type": "mcq",
        "is_parametric": True,
        "prompt": prompt,
        "options": options,
        "correct_index": options.index(correct_str),
        "hint": hint,
        "explanation": explanation,
    }


def _legacy_options(correct_str, wrong_strs):
    options = [correct_str]
    for w in wrong_strs:
        if w not in options:
            options.append(w)
        if len(options) == 4:
            break
    while len(options) < 4:
        filler = f"${random.randint(-15, 25)}$"
        if filler not in options:
            options.append(filler)
    random.shuffle(options)
    return options


def gen_inequality_abs(variant=None, *, rng=random):
    v = variant % 4 if variant is not None else rng.randrange(4)
    if v == 0:
        a = rng.randint(2, 5)
        x_center = rng.randint(-4, 5)
        r = rng.randint(2, 6)
        b = a * x_center
        rad = a * r
        low = x_center - r
        high = x_center + r
        sign_b = f"- {b}" if b > 0 else (f"+ {-b}" if b < 0 else "")
        prompt = f"Resuelva en $\\mathbb{{R}}$ la inecuación con valor absoluto $|{a}x {sign_b}| < {rad}$."
        correct = f"$({low},\\; {high})$"
        wrongs = [
            f"$[{low},\\; {high}]$",
            f"$(-\\infty, {low}) \\cup ({high}, \\infty)$",
            f"$(-\\infty, {high})$",
        ]
        hint = f"Escribe $-{rad} < {a}x {sign_b} < {rad}$ y despeja $x$."
        explanation = (
            f"Descomponemos como $-{rad} < {a}x {sign_b} < {rad}$. Sumando ${b}$ obtenemos "
            f"${b - rad} < {a}x < {b + rad}$, y dividiendo por ${a} > 0$ resulta $x \\in ({low}, {high})$. "
            "Error típico: elegir los intervalos exteriores, que corresponden a distancias mayores."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
    elif v == 1:
        r1 = rng.randint(-4, 0)
        r2 = rng.randint(2, 6)
        s1 = f"+ {-r1}" if r1 < 0 else (f"- {r1}" if r1 > 0 else "")
        prompt = f"¿Cuál es el conjunto solución en $\\mathbb{{R}}$ de la inecuación racional $\\frac{{x - {r2}}}{{x {s1}}} \\le 0$?"
        correct = f"$({r1},\\; {r2}]$"
        wrongs = [
            f"$[{r1},\\; {r2}]$",
            f"$(-\\infty, {r1}) \\cup [{r2}, \\infty)$",
            f"$({r1},\\; {r2})$",
        ]
        hint = f"Los puntos críticos son $x = {r1}$ (excluido por anular el denominador) y $x = {r2}$ (incluido)."
        explanation = (
            f"Para $x < {r1}$ ambos factores son negativos. En $({r1}, {r2})$ el numerador es negativo y el denominador positivo. "
            f"Para $x > {r2}$ ambos son positivos. Incluimos $x = {r2}$ porque el cociente vale cero. "
            f"Error típico: incluir $x = {r1}$, donde el denominador vale cero. La solución es $({r1}, {r2}]$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
    elif v == 2:
        c = rng.randint(3, 8)
        k = rng.randint(2, 6)
        inf_val = c - k
        sup_val = c
        prompt = (
            f"Sea el conjunto $S = \\left\\{{ {c} - \\frac{{{k}}}{{n}} : n \\in \\mathbb{{N}}_{{\\ge 1}} \\right\\}}$. "
            f"Determine $\\inf(S)$ y $\\sup(S)$."
        )
        correct = f"$\\inf(S) = {inf_val},\\; \\sup(S) = {sup_val}$"
        wrongs = [
            f"$\\inf(S) = {c},\\; \\sup(S) = {c + k}$",
            f"$\\inf(S) = {inf_val},\\; \\sup(S) = {c + k}$",
            f"$\\inf(S) = {-k},\\; \\sup(S) = {sup_val}$",
        ]
        hint = "Evalúa el primer término en $n = 1$ y toma el límite cuando $n \\to \\infty$."
        explanation = (
            f"Como ${k}/n$ disminuye con $n$, la sucesión crece. Su mínimo e ínfimo es $x_1 = {c}-{k} = {inf_val}$. "
            f"Todos los términos están por debajo de ${sup_val}$ y se acercan tanto como se quiera a ese valor "
            f"porque ${k}/n \\to 0$. El supremo es ${sup_val}$. Error típico: confundir el supremo con un máximo alcanzado."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
    else:
        c = rng.randint(3, 8)
        k = rng.randint(2, 6)
        m = rng.randint(2, 9)
        threshold = k * m
        prompt = (
            f"Sea $a_n = {c} - \\frac{{{k}}}{{n}}$ para enteros $n \\ge 1$. "
            f"¿Cuál es el menor entero $N \\ge 1$ tal que $|a_n - {c}| < \\frac{{1}}{{{m}}}$ para todo $n \\ge N$?"
        )
        correct = f"${threshold + 1}$"
        wrongs = [f"${threshold}$", f"${m + 1}$", f"${threshold + 2}$"]
        hint = "Calcula la distancia al límite y despeja $n$ usando que todos los denominadores son positivos."
        explanation = (
            f"La distancia es $|a_n - {c}| = {k}/n$. Multiplicando $\\frac{{{k}}}{{n}} < \\frac{{1}}{{{m}}}$ "
            f"por $n \\cdot {m} > 0$ obtenemos $n > {threshold}$. El primer entero que cumple es $N = {threshold + 1}$ "
            f"y todos los siguientes también cumplen. Error típico: elegir $N = {threshold}$, donde se alcanza la igualdad."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)


def _fraction_latex(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"\\frac{{{value.numerator}}}{{{value.denominator}}}"


def gen_function_composition(variant=None, *, rng=random):
    v = variant if variant is not None else rng.randrange(3)
    if v % 3 == 0:
        a = rng.randint(2, 5)
        b = rng.randint(1, 6)
        c = rng.randint(2, 4)
        x0 = rng.randint(1, 4)
        fx0 = a * x0 + b
        gfx0 = fx0 * fx0 - c
        fgx0 = a * (x0 * x0 - c) + b
        prompt = (
            f"Sean $f(x) = {a}x + {b}$ y $g(x) = x^2 - {c}$. "
            f"Calcule el valor de la función compuesta $(g \\circ f)({x0}) = g(f({x0}))$."
        )
        correct = f"${gfx0}$"
        wrongs = [
            f"${fgx0}$",
            f"${fx0 * fx0}$",
            f"${gfx0 + 2 * c}$",
        ]
        hint = f"Evalúa primero la función interna $u = f({x0})$ y luego calcula $g(u)$."
        explanation = (
            f"Primero calculamos $f({x0}) = {a}({x0}) + {b} = {fx0}$. "
            f"Luego evaluamos $g({fx0}) = ({fx0})^2 - {c} = {fx0*fx0} - {c} = {gfx0}$. "
            "Error típico: invertir el orden y calcular $(f \\circ g)$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
    elif v % 3 == 1:
        a = rng.randint(2, 5)
        b = rng.randint(1, 7)
        x_inv = rng.randint(2, 6)
        y0 = a * x_inv + b
        prompt = (
            f"Sea $f: \\mathbb{{R}} \\to \\mathbb{{R}}$ la función biyectiva $f(x) = {a}x + {b}$. "
            f"Calcule el valor de la función inversa $f^{{-1}}({y0})$."
        )
        correct = f"${x_inv}$"
        wrongs = [
            f"${a * y0 + b}$",
            f"${_fraction_latex(Fraction(y0 + b, a))}$",
            f"$\\frac{{1}}{{{a * y0 + b}}}$",
        ]
        hint = f"Busca el único $x \\in \\mathbb{{R}}$ tal que $f(x) = {a}x + {b} = {y0}$."
        explanation = (
            f"Resolvemos ${a}x + {b} = {y0} \\implies {a}x = {y0 - b} \\implies x = {x_inv}$. "
            f"Por tanto, $f^{{-1}}({y0}) = {x_inv}$. Error típico: tomar el recíproco $1/f({y0})$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
    else:
        h = rng.randint(1, 5)
        k = rng.randint(1, 6)
        b_coef = -2 * h
        c_coef = h * h + k
        prompt = (
            f"Sea $f(x) = x^2 {b_coef}x + {c_coef}$ restringida al dominio $[{h}, +\\infty)$ donde es inyectiva. "
            f"¿Cuál es su recorrido $\\text{{Rec}}(f)$?"
        )
        correct = f"$[{k},\\; +\\infty)$"
        wrongs = [
            f"$({k},\\; +\\infty)$",
            f"$[{c_coef},\\; +\\infty)$",
            f"$(-\\infty,\\; {k}]$",
        ]
        hint = f"Completa el cuadrado: $f(x) = (x - {h})^2 + {k}$."
        explanation = (
            f"Completando el cuadrado obtenemos $f(x) = (x - {h})^2 + {k}$. "
            f"El mínimo es $f({h}) = {k}$. Cada $y \\ge {k}$ se alcanza tomando $x = {h} + \\sqrt{{y-{k}}}$ "
            f"en el dominio. Así, el recorrido es $[{k}, +\\infty)$. Error típico: excluir el mínimo."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)


def gen_limit_rational(variant=None, *, rng=random):
    v = variant if variant is not None else rng.randrange(3)
    if v % 3 == 0:
        r1 = rng.randint(1, 5)
        r2 = rng.choice([i for i in range(-5, 6) if i != r1])
        b_coef = -(r1 + r2)
        c_coef = r1 * r2
        val = r1 - r2
        b_str = f"+ {b_coef}x" if b_coef > 0 else (f"- {-b_coef}x" if b_coef < 0 else "")
        c_str = f"+ {c_coef}" if c_coef > 0 else (f"- {-c_coef}" if c_coef < 0 else "")
        prompt = f"Calcule el límite $\\lim_{{x \\to {r1}}} \\frac{{x^2 {b_str} {c_str}}}{{x - {r1}}}$."
        correct = f"${val}$"
        wrongs = [
            f"${-val}$",
            "$0$",
            "No existe",
        ]
        hint = f"Factoriza el numerador como $(x - {r1})(x - ({r2}))$ para cancelar la indeterminación $0/0$."
        explanation = (
            f"Factorizando el numerador: $\\frac{{(x - {r1})(x - ({r2}))}}{{x - {r1}}} = x - ({r2})$ para $x \\neq {r1}$. "
            f"Al tomar $x \\to {r1}$ obtenemos ${r1} - ({r2}) = {val}$. "
            f"Error típico: concluir que el límite no existe porque la función no está definida en $x={r1}$."
        )
        question = _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
        question["fire_audit"] = "limite_factorizado"
        return question
    elif v % 3 == 1:
        a = rng.randint(2, 5)
        k = rng.choice([2, 4, 6])
        answer = _fraction_latex(Fraction(k, 2 * a))
        domain_start = _fraction_latex(Fraction(-a * a, k))
        prompt = f"Calcule sin usar L'Hôpital: $\\lim_{{x \\to 0}} \\frac{{\\sqrt{{{a*a} + {k}x}} - {a}}}{{x}}$."
        correct = f"${answer}$"
        wrongs = [
            f"${_fraction_latex(Fraction(k, a))}$",
            f"${k * a}$",
            "$0$",
        ]
        hint = f"Multiplica numerador y denominador por el conjugado $\\sqrt{{{a*a} + {k}x}} + {a}$."
        explanation = (
            f"El radical está definido para $x \\ge {domain_start}$, así que podemos acercarnos a cero desde ambos lados. "
            f"Para $x \\ne 0$, racionalizamos y cancelamos $x$: $\\frac{{({a*a}+{k}x) - {a*a}}}{{x(\\sqrt{{{a*a}+{k}x}}+{a})}} = "
            f"\\frac{{{k}}}{{\\sqrt{{{a*a}+{k}x}}+{a}}}$. En el límite queda $\\frac{{{k}}}{{{a}+{a}}}={answer}$. "
            f"Error típico: contar solo una vez el término ${a}$ del denominador."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
    else:
        p = rng.choice([3, 5, 6, 8, 9])
        q = rng.choice([2, 4, 7])
        answer = _fraction_latex(Fraction(p, q))
        prompt = f"Con ángulos en radianes, calcule $\\lim_{{x \\to 0}} \\frac{{\\sin({p}x)}}{{{q}x}}$."
        correct = f"${answer}$"
        wrongs = [
            f"${_fraction_latex(Fraction(q, p))}$",
            "$1$",
            "$0$",
        ]
        hint = f"Reescribe como $\\frac{{{p}}}{{{q}}} \\cdot \\frac{{\\sin({p}x)}}{{{p}x}}$ y usa $\\lim_{{u\\to 0}} \\frac{{\\sin u}}{{u}} = 1$."
        explanation = (
            f"Multiplicando y dividiendo por ${p}$: $\\lim_{{x\\to 0}} \\frac{{{p}}}{{{q}}}\\frac{{\\sin({p}x)}}{{{p}x}} = "
            f"\\frac{{{p}}}{{{q}}} \\cdot 1 = {answer}$. "
            f"Error típico: aplicar el límite notable sin conservar el factor $\\frac{{{p}}}{{{q}}}$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)


def gen_continuity_param(variant=None, *, rng=random):
    v = variant if variant is not None else rng.randrange(2)
    if v % 2 == 0:
        x0 = rng.randint(1, 3)
        c = rng.randint(1, 5)
        a_val = 2 * x0
        b_val = (x0 * x0 + c) - a_val * x0
        prompt = (
            f"Determine $(a, b)$ para que $f(x) = \\begin{{cases}} x^2 + {c} & x \\le {x0} \\\\ ax + b & x > {x0} \\end{{cases}}$ "
            f"sea continua y derivable en $x = {x0}$."
        )
        correct = f"$a = {a_val},\\; b = {b_val}$"
        wrongs = [
            f"$a = {a_val},\\; b = {x0 * x0 + c}$",
            f"$a = {x0},\\; b = {c}$",
            f"$a = {a_val},\\; b = {c}$",
        ]
        hint = f"Exige primero continuidad en $x={x0}$. Luego compara los límites laterales del cociente incremental."
        explanation = (
            f"La continuidad exige ${x0}a+b = {x0*x0+c}$. Con esa igualdad, el cociente incremental para $h>0$ es $a$. "
            f"Para $h<0$ es $\\frac{{({x0}+h)^2-{x0}^2}}{{h}} = {a_val}+h$. "
            f"Los límites coinciden si $a={a_val}$. Al sustituir en la condición de continuidad resulta $b={b_val}$. "
            "Error típico: igualar las pendientes sin comprobar que los tramos coinciden en el empalme."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
    else:
        a = rng.randint(2, 4)
        x0 = rng.randint(1, 3)
        slope = 3 * (x0 ** 2) - a
        prompt = (
            f"Usando la definición de derivada, ¿cuál es la pendiente de la recta tangente a la curva "
            f"$f(x) = x^3 - {a}x + 2$ en el punto $x_0 = {x0}$?"
        )
        correct = f"${slope}$"
        wrongs = [
            f"${3 * (x0 ** 2) + a}$",
            f"${3 * x0 ** 2}$",
            f"${x0 ** 2 - a}$",
        ]
        hint = f"Expande $({x0}+h)^3$ en el cociente $[f({x0}+h)-f({x0})]/h$."
        explanation = (
            f"Al restar, el término constante desaparece: $f({x0}+h)-f({x0}) = (3\\cdot {x0}^2-{a})h+3\\cdot {x0}h^2+h^3$. "
            f"Dividimos por $h\\ne 0$ y tomamos $h\\to 0$. Queda $f'({x0}) = 3\\cdot {x0}^2-{a} = {slope}$. "
            f"Error típico: omitir el aporte $-{a}$ del término lineal."
        )
        question = _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
        question["fire_audit"] = "derivada_por_definicion"
        return question


def gen_continuous_radical_extension(*, rng):
    b = rng.randint(1, 6)
    root = rng.randint(2, 6)
    a = b + root**2
    expression = f"\\sqrt{{\\frac{{x^2-{a+b}x+{a*b}}}{{x-{a}}}}}"
    domain = f"[{b},\\infty)\\setminus\\{{{a}\\}}"
    prompt = (
        f"Para $x\\ne {a}$ se define $f(x)={expression}$ donde la expresión es real. "
        f"¿Cuál es el dominio natural de la expresión original y qué valor debe tomar "
        f"$f({a})$ para extenderla por continuidad?"
    )
    correct = f"$D={domain},\\quad f({a})={root}$"
    wrongs = [
        f"$D=[{b},\\infty),\\quad f({a})={root}$",
        f"$D=({b},\\infty)\\setminus\\{{{a}\\}},\\quad f({a})={root}$",
        f"$D={domain},\\quad f({a})={root**2}$",
    ]
    hint = "Factoriza el numerador antes de analizar el signo del radicando. Conserva la restricción del denominador."
    explanation = (
        f"El numerador es $(x-{a})(x-{b})$. Para $x\\ne {a}$ el radicando se reduce a $x-{b}$, "
        f"que es no negativo si $x\\ge {b}$. El dominio original es ${domain}$. "
        f"Como ${a}>{b}$, hay puntos del dominio a ambos lados de ${a}$. "
        f"El límite de $\\sqrt{{x-{b}}}$ al acercarse a ${a}$ es $\\sqrt{{{root**2}}}={root}$. "
        f"Error típico: incluir ${a}$ en el dominio original al cancelar el denominador."
    )
    question = _make_mcq(prompt, correct, wrongs, hint, explanation, rng=rng)
    question["fire_audit"] = "extension_radical"
    return question


def gen_logic_truth(variant=None):
    variants = [
        (
            "¿Cuál es la negación formal de la proposición $(\\forall x \\in A,\\; P(x)) \\implies Q$?",
            "$(\\forall x \\in A,\\; P(x)) \\;\\land\\; \\neg Q$",
            [
                "$(\\exists x \\in A,\\; \\neg P(x)) \\implies \\neg Q$",
                "$(\\exists x \\in A,\\; \\neg P(x)) \\;\\land\\; \\neg Q$",
                "$\\neg Q \\implies (\\exists x \\in A,\\; \\neg P(x))$",
            ],
            "Recuerda que $\\neg(A \\implies B) \\equiv A \\land \\neg B$; el antecedente $A$ queda intacto.",
            "Aplicando $\\neg(R \\implies Q) \\equiv R \\land \\neg Q$ con $R = (\\forall x \\in A, P(x))$, obtenemos $(\\forall x \\in A, P(x)) \\land \\neg Q$.",
        ),
        (
            "Si sabemos que $p \\implies q$ es Falsa, ¿cuáles son los valores de verdad de $p$ y $q$ respectivamente?",
            "$p$ es Verdadera y $q$ es Falsa",
            [
                "$p$ es Falsa y $q$ es Verdadera",
                "$p$ es Falsa y $q$ es Falsa",
                "$p$ es Verdadera y $q$ es Verdadera",
            ],
            "Una implicancia solo falla cuando la hipótesis se cumple pero la conclusión no.",
            "Por definición de tabla de verdad, $p \\implies q \\equiv \\neg p \\lor q$ es Falsa única y exclusivamente cuando $p = V$ y $q = F$.",
        ),
        (
            "¿Cuál es la negación lógica de $\\exists x \\in \\mathbb{R},\\; (P(x) \\land \\neg Q(x))$?",
            "$\\forall x \\in \\mathbb{R},\\; (P(x) \\implies Q(x))$",
            [
                "$\\forall x \\in \\mathbb{R},\\; (\\neg P(x) \\land Q(x))$",
                "$\\exists x \\in \\mathbb{R},\\; (P(x) \\implies Q(x))$",
                "$\\forall x \\in \\mathbb{R},\\; (Q(x) \\implies P(x))$",
            ],
            "Aplica De Morgan a $\\neg(P(x) \\land \\neg Q(x)) \\equiv \\neg P(x) \\lor Q(x) \\equiv P(x) \\implies Q(x)$.",
            "Al negar el cuantificador existencial obtenemos $\\forall x$, y por De Morgan $\\neg(P \\land \\neg Q) \\equiv \\neg P \\lor Q \\equiv (P \\implies Q)$.",
        ),
    ]
    idx = (variant if variant is not None else random.randint(0, len(variants) - 1)) % len(variants)
    p, c, w, h, e = variants[idx]
    return _make_mcq(p, c, w, h, e)


def gen_summation_telescopic(variant=None):
    v = variant if variant is not None else random.randint(0, 2)
    if v % 3 == 0:
        n = random.choice([10, 12, 15, 20, 25, 30])
        c = random.randint(1, 6)
        ans = n * (n + 1) + c * n
        prompt = f"Calcule el valor exacto de la sumatoria $\\sum_{{k=1}}^{{{n}}} (2k + {c})$."
        correct = f"${ans}$"
        wrongs = [
            f"${n * (n + 1) // 2 + c * n}$",
            f"${n * (n + 1) + c}$",
            f"${ans + n}$",
        ]
        hint = f"Separa por linealidad: $2\\sum_{{k=1}}^{{{n}}} k + \\sum_{{k=1}}^{{{n}}} {c} = 2\\frac{{{n}({n}+1)}}{{2}} + {c}\\cdot {n}$."
        explanation = (
            f"Por linealidad: $2 \\cdot \\frac{{{n}({n+1})}}{{2}} + {c}({n}) = {n*(n+1)} + {c*n} = {ans}$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation)
    elif v % 3 == 1:
        n = random.choice([8, 10, 12, 15, 20, 24])
        a = random.choice([2, 3, 4])
        # sum_{k=1}^n 1/((k+a-1)(k+a)) = 1/a - 1/(n+a) = n / (a*(n+a))
        num = n
        den = a * (n + a)
        g = math.gcd(num, den)
        num_s, den_s = num // g, den // g
        term_str = f"\\frac{{1}}{{(k+{a-1})(k+{a})}}"
        prompt = f"Usando la propiedad telescópica, calcule el valor exacto de $\\sum_{{k=1}}^{{{n}}} {term_str}$."
        correct = f"$\\frac{{{num_s}}}{{{den_s}}}$"
        wrongs = [
            f"$\\frac{{{1}}}{{{n + a}}}$",
            f"$\\frac{{{n + 1}}}{{{den}}}$",
            f"$\\frac{{{num_s}}}{{{den_s + 1}}}$",
        ]
        hint = f"Usa fracciones parciales: $\\frac{{1}}{{(k+{a-1})(k+{a})}} = \\frac{{1}}{{k+{a-1}}} - \\frac{{1}}{{k+{a}}}$."
        explanation = (
            f"Al descomponer en suma telescópica se cancelan los términos intermedios, quedando "
            f"$\\frac{{1}}{{{a}}} - \\frac{{1}}{{{n}+{a}}} = \\frac{{{n}}}{{{a}({n+a})}} = \\frac{{{num_s}}}{{{den_s}}}$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation)
    else:
        n = random.choice([5, 6, 7, 8])
        k = random.choice([2, 3])
        a = random.choice([2, 3])
        coef = math.comb(n, k) * (a ** k)
        prompt = (
            f"Por el Teorema del Binomio de Newton, ¿cuál es el coeficiente de $x^{{{k}}}$ en el desarrollo de $(1 + {a}x)^{{{n}}}$?"
        )
        correct = f"${coef}$"
        wrongs = [
            f"${math.comb(n, k) * a}$",
            f"${math.comb(n, k)}$",
            f"${(a ** k) * n}$",
        ]
        hint = f"El término con $x^{{{k}}}$ en $(1 + {a}x)^{{{n}}}$ es $\\binom{{{n}}}{{{k}}} ({a}x)^{{{k}}} = \\binom{{{n}}}{{{k}}} {a}^{{{k}}} x^{{{k}}}$."
        explanation = (
            f"Por el Teorema del Binomio, el coeficiente de $x^{{{k}}}$ es "
            f"$\\binom{{{n}}}{{{k}}} \\cdot {a}^{{{k}}} = {math.comb(n, k)} \\cdot {a**k} = {coef}$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_vectors_dot_proj(variant=None):
    v = variant if variant is not None else random.randint(0, 1)
    if v % 2 == 0:
        u1, u2, u3 = random.randint(1, 4), random.randint(-3, 3), random.randint(1, 4)
        v1, v2 = random.randint(1, 3), random.randint(1, 3)
        v3 = random.randint(-2, 3)
        dot = u1 * v1 + u2 * v2 + u3 * v3
        prompt = (
            f"Dados los vectores $u = ({u1}, {u2}, {u3})$ y $v = ({v1}, {v2}, {v3})$ en $\\mathbb{{R}}^3$, "
            f"calcule el producto punto $u \\cdot v$."
        )
        correct = f"${dot}$"
        wrongs = [
            f"${dot + 2 * u1}$",
            f"${abs(dot) + 3}$",
            f"${u1 + u2 + u3 + v1 + v2 + v3}$",
        ]
        hint = "Multiplica componente a componente y suma: $u_1 v_1 + u_2 v_2 + u_3 v_3$."
        explanation = f"$u \\cdot v = ({u1})({v1}) + ({u2})({v2}) + ({u3})({v3}) = {u1*v1} + ({u2*v2}) + ({u3*v3}) = {dot}$."
        return _make_mcq(prompt, correct, wrongs, hint, explanation)
    else:
        u1, u2 = random.choice([2, 3, 4]), random.choice([1, 2, 3])
        v2 = random.choice([2, 4])
        # u = (u1, u2, -1), v = (v1, v2, k) ortogonales => u1*1 + u2*v2 - k = 0 => k = u1 + u2*v2
        k_val = u1 + u2 * v2
        prompt = (
            f"¿Para qué valor de $\\alpha \\in \\mathbb{{R}}$ los vectores $u = ({u1}, {u2}, -1)$ y "
            f"$v = (1, {v2}, \\alpha)$ en $\\mathbb{{R}}^3$ son ortogonales?"
        )
        correct = f"$\\alpha = {k_val}$"
        wrongs = [
            f"$\\alpha = {-k_val}$",
            f"$\\alpha = {u1 * v2 - u2}$",
            "$\\alpha = 0$",
        ]
        hint = "Dos vectores son ortogonales si y solo si su producto punto $u \\cdot v = 0$."
        explanation = (
            f"Imponemos $u \\cdot v = ({u1})(1) + ({u2})({v2}) + (-1)(\\alpha) = {k_val} - \\alpha = 0 \\implies \\alpha = {k_val}$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_complex_modulus(variant=None):
    v = variant if variant is not None else random.randint(0, 1)
    if v % 2 == 0:
        a, b = random.choice([(3, 4), (5, 12), (6, 8)])
        n = random.choice([2, 3, 4])
        mod_sq = a * a + b * b
        r = int(math.isqrt(mod_sq))
        ans = r ** n
        prompt = f"Sea $z = {a} - {b}i \\in \\mathbb{{C}}$. ¿Cuál es el módulo $|z^{n}|$?"
        correct = f"${ans}$"
        wrongs = [f"${r * n}$", f"${mod_sq ** n}$", f"${(a + b) ** n}$"]
        hint = f"Usa la propiedad multiplicativa del módulo: $|z^{n}| = |z|^{n}$ con $|z| = \\sqrt{{{a}^2 + (-{b})^2}}$."
        explanation = f"Como $|z| = \\sqrt{{{a}^2 + (-{b})^2}} = \\sqrt{{{mod_sq}}} = {r}$, entonces $|z^{n}| = |z|^{n} = {r}^{n} = {ans}$."
        return _make_mcq(prompt, correct, wrongs, hint, explanation)
    else:
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        re_sum = 2 * a
        mod_sq = a * a + b * b
        prompt = (
            f"Si $z_1 = {a} + {b}i$ es una raíz compleja de un polinomio mónico $P(x) = x^2 + px + q$ con coeficientes reales, "
            f"¿cuáles son los valores de $p$ y $q$?"
        )
        correct = f"$p = {-re_sum},\\; q = {mod_sq}$"
        wrongs = [
            f"$p = {re_sum},\\; q = {mod_sq}$",
            f"$p = {-re_sum},\\; q = {a*a - b*b}$",
            f"$p = {-a},\\; q = {b*b}$",
        ]
        hint = f"Por coeficientes reales, la otra raíz es el conjugado $z_2 = {a} - {b}i$, y $P(x) = (x - z_1)(x - \\bar{{z}}_1) = x^2 - 2\\text{{Re}}(z_1)x + |z_1|^2$."
        explanation = (
            f"Las raíces conjugadas suman $z_1 + \\bar{{z}}_1 = {re_sum} = -p \\implies p = {-re_sum}$, "
            f"y su producto es $z_1\\bar{{z}}_1 = {a}^2 + {b}^2 = {mod_sq} = q$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_descriptive_stats(variant=None):
    v = variant if variant is not None else random.randint(0, 1)
    if v % 2 == 0:
        mean_x = random.randint(5, 20)
        sd_x = random.randint(2, 6)
        a = random.choice([-3, -2, 2, 3, 4])
        b = random.randint(1, 10)
        mean_y = a * mean_x + b
        var_y = (a * a) * (sd_x * sd_x)
        prompt = (
            f"Una variable $X$ tiene media muestral $\\bar{{x}} = {mean_x}$ y desviación estándar $s_x = {sd_x}$. "
            f"Si definimos $Y = {a}X + {b}$, ¿cuáles son la media $\\bar{{y}}$ y la varianza $s_y^2$?"
        )
        correct = f"$\\bar{{y}} = {mean_y},\\; s_y^2 = {var_y}$"
        wrongs = [
            f"$\\bar{{y}} = {mean_y},\\; s_y^2 = {abs(a) * sd_x * sd_x + b}$",
            f"$\\bar{{y}} = {a * mean_x},\\; s_y^2 = {a * sd_x * sd_x}$",
            f"$\\bar{{y}} = {mean_y},\\; s_y^2 = {abs(a) * sd_x}$",
        ]
        hint = "La media es lineal ($\\bar{y} = a\\bar{x} + b$), pero la varianza cumple $s_y^2 = a^2 s_x^2$ (la constante $+b$ no afecta la dispersión)."
        explanation = (
            f"$\\bar{{y}} = {a}({mean_x}) + {b} = {mean_y}$. "
            f"Como $s_x^2 = {sd_x}^2 = {sd_x*sd_x}$, la nueva varianza es $s_y^2 = ({a})^2 s_x^2 = {a*a} \\cdot {sd_x*sd_x} = {var_y}$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation)
    else:
        n_total = random.choice([7, 8, 9, 10])
        k_pick = random.choice([2, 3])
        ans = math.comb(n_total, k_pick)
        perm = math.perm(n_total, k_pick)
        prompt = (
            f"En un proyecto de Ciencia de Datos con ${n_total}$ variables candidatas, "
            f"¿de cuántas formas distintas se puede elegir un subconjunto de ${k_pick}$ variables (sin importar el orden)?"
        )
        correct = f"${ans}$"
        wrongs = [
            f"${perm}$",
            f"${n_total * k_pick}$",
            f"${n_total ** k_pick}$",
        ]
        hint = f"Como no importa el orden de selección, calcula el coeficiente binomial $\\binom{{{n_total}}}{{{k_pick}}}$."
        explanation = (
            f"El número de subconjuntos de tamaño ${k_pick}$ es $\\binom{{{n_total}}}{{{k_pick}}} = "
            f"\\frac{{{n_total}!}}{{{k_pick}!({n_total-k_pick})!}} = {ans}$."
        )
        return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_derivative_chain():
    k = random.randint(2, 6)
    p = random.randint(3, 5)
    # f(x) = (k*x^2 + 1)^p at x = 1 => f'(1) = p*(k+1)^(p-1) * (2k)
    val_in = k + 1
    deriv = p * (val_in ** (p - 1)) * (2 * k)
    wrong_no_chain = p * (val_in ** (p - 1))
    prompt = f"Sea $f(x) = ({k}x^2 + 1)^{{{p}}}$. Calcule el valor de la derivada $f'(1)$."
    correct = f"${deriv}$"
    wrongs = [
        f"${wrong_no_chain}$",
        f"${p * (2 * k) ** (p - 1)}$",
        f"${deriv // 2}$",
    ]
    hint = f"Por regla de la cadena, $f'(x) = {p}({k}x^2 + 1)^{{{p-1}}} \\cdot (2\\cdot {k}x)$."
    explanation = (
        f"Derivando con regla de la cadena: $f'(x) = {p}({k}x^2 + 1)^{{{p-1}}} \\cdot ({2*k}x)$. "
        f"Evaluando en $x = 1$: $f'(1) = {p}({val_in})^{{{p-1}}} \\cdot {2*k} = {deriv}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_taylor_opt_1d():
    a = random.randint(2, 5)
    # f(x) = x^2 - 2*a*x + a^2 + b => min at x = a
    b = random.randint(1, 9)
    c_term = a * a + b
    prompt = f"Considere la función de costo $L(w) = w^2 - {2*a}w + {c_term}$. ¿En qué punto $w^*$ alcanza su mínimo global y cuál es el valor mínimo $L(w^*)$?"
    correct = f"$w^* = {a},\\; L(w^*) = {b}$"
    wrongs = [
        f"$w^* = {-a},\\; L(w^*) = {b}$",
        f"$w^* = {2*a},\\; L(w^*) = {c_term}$",
        f"$w^* = {a},\\; L(w^*) = {c_term}$",
    ]
    hint = "Iguala la derivada $L'(w) = 2w - 2a = 0$ (o completa el cuadrado $(w - a)^2 + b$)."
    explanation = (
        f"Derivando: $L'(w) = 2w - {2*a} = 0 \\implies w^* = {a}$ (con $L''(w) = 2 > 0$, mínimo estricto). "
        f"Al evaluar: $L({a}) = ({a} - {a})^2 + {b} = {b}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_definite_integral():
    k = random.randint(2, 5)
    m = random.randint(2, 4)
    # d/dx int_0^{x^m} cos(k t) dt
    prompt = f"Usando el Teorema Fundamental del Cálculo, calcule $F'(x)$ para $F(x) = \\int_{{0}}^{{x^{m}}} \\cos({k}t)\\,dt$."
    correct = f"${m}x^{{{m-1}}} \\cos({k}x^{{{m}}})$"
    wrongs = [
        f"$\\cos({k}x^{{{m}}})$",
        f"$-{m}x^{{{m-1}}} \\sin({k}x^{{{m}}})$",
        f"$\\frac{{1}}{{{k}}}\\sin({k}x^{{{m}}})$",
    ]
    hint = "Por regla de Leibniz (TFC + Regla de la Cadena): $\\frac{d}{dx}\\int_0^{h(x)} f(t)dt = f(h(x)) \\cdot h'(x)$."
    explanation = (
        f"Evaluamos el integrando $f(t) = \\cos({k}t)$ en el límite superior $h(x) = x^{{{m}}}$ "
        f"y multiplicamos por $h'(x) = {m}x^{{{m-1}}}$, obteniendo ${m}x^{{{m-1}}}\\cos({k}x^{{{m}}})$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_matrix_rank_system():
    a = random.randint(2, 5)
    mult = random.randint(2, 4)
    k_val = a * mult
    prompt = (
        f"¿Para qué valor de $k \\in \\mathbb{{R}}$ la matriz $A = \\begin{{pmatrix}} 1 & {a} \\\\ {mult} & k \\end{{pmatrix}}$ "
        f"no es invertible (tiene rango $< 2$)?"
    )
    correct = f"$k = {k_val}$"
    wrongs = [
        f"$k = {-k_val}$",
        f"$k = {a + mult}$",
        "$k = 0$",
    ]
    hint = "Una matriz cuadrada no es invertible si y solo si su determinante es $0$ (o sus filas son proporcionales)."
    explanation = f"Calculamos $\\det(A) = 1\\cdot k - {a}\\cdot {mult} = k - {k_val} = 0 \\implies k = {k_val}$."
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_rank_nullity():
    m = random.randint(4, 8)
    n = random.randint(5, 10)
    r = random.randint(2, min(m, n) - 1)
    nullity = n - r
    prompt = (
        f"Sea $A \\in \\mathbb{{R}}^{{{m} \\times {n}}}$ una matriz de datos con $\\text{{rango}}(A) = {r}$. "
        f"Por el Teorema del Rango-Nulidad, ¿cuál es la dimensión del núcleo $\\dim(\\ker A)$?"
    )
    correct = f"${nullity}$"
    wrongs = [
        f"${m - r}$",
        f"${r}$",
        f"${n + m - r}$",
    ]
    hint = "Recuerda que $\\dim(\\ker A) + \\text{rango}(A) = n$, donde $n$ es el número de columnas."
    explanation = f"El número de columnas es $n = {n}$. Por Rango-Nulidad: $\\dim(\\ker A) = n - \\text{{rango}}(A) = {n} - {r} = {nullity}$."
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_least_squares_1d():
    y1 = random.randint(1, 5)
    y2 = random.randint(2, 6)
    # ajustar modelo constante o lineal x=(1, 2)^T, b=(y1, y2)^T => A^TA = 5, A^Tb = y1 + 2*y2
    ata = 5
    atb = y1 + 2 * y2
    prompt = (
        f"Para ajustar $y = \\beta x$ por Mínimos Cuadrados a los datos $(1, {y1})$ y $(2, {y2})$, "
        f"planteamos $A = \\begin{{pmatrix}} 1 \\\\ 2 \\end{{pmatrix}}$ y $b = \\begin{{pmatrix}} {y1} \\\\ {y2} \\end{{pmatrix}}$. "
        f"¿Cuál es el estimador óptimo $\\hat{{\\beta}} = (A^TA)^{{-1}}A^Tb$?"
    )
    correct = f"$\\frac{{{atb}}}{{5}}$"
    wrongs = [
        f"$\\frac{{{y1 + y2}}}{{3}}$",
        f"$\\frac{{{atb}}}{{3}}$",
        f"$\\frac{{{2*y1 + y2}}}{{5}}$",
    ]
    hint = "Calcula $A^T A = 1^2 + 2^2 = 5$ y $A^T b = 1\\cdot y_1 + 2\\cdot y_2$."
    explanation = f"Tenemos $A^T A = 1^2 + 2^2 = 5$ y $A^T b = 1({y1}) + 2({y2}) = {atb}$. De $5\\hat{{\\beta}} = {atb}$ resulta $\\hat{{\\beta}} = \\frac{{{atb}}}{{5}}$."
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_eigenvalues_2x2():
    l1 = random.randint(1, 5)
    l2 = random.randint(l1 + 1, 8)
    # Matriz triangular o simétrica sencilla con valores propios l1 y l2
    tr = l1 + l2
    det = l1 * l2
    prompt = (
        f"Si una matriz $A \\in \\mathbb{{R}}^{{2 \\times 2}}$ tiene traza $\\text{{tr}}(A) = {tr}$ y determinante $\\det(A) = {det}$, "
        f"¿cuáles son sus valores propios $\\lambda_1, \\lambda_2$?"
    )
    correct = f"$\\lambda_1 = {l1},\\; \\lambda_2 = {l2}$"
    wrongs = [
        f"$\\lambda_1 = {-l1},\\; \\lambda_2 = {-l2}$",
        f"$\\lambda_1 = {tr},\\; \\lambda_2 = {det}$",
        f"$\\lambda_1 = {l1 - 1},\\; \\lambda_2 = {l2 + 1}$",
    ]
    hint = "Busca dos números cuya suma sea la traza y cuyo producto sea el determinante: $\\lambda^2 - \\text{tr}(A)\\lambda + \\det(A) = 0$."
    explanation = (
        f"El polinomio característico es $\\lambda^2 - {tr}\\lambda + {det} = (\\lambda - {l1})(\\lambda - {l2}) = 0$, "
        f"por lo que los valores propios son ${l1}$ y ${l2}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_gradient_eval():
    a = random.randint(2, 5)
    b = random.randint(1, 4)
    x0 = random.randint(1, 3)
    y0 = random.randint(1, 3)
    # f(x,y) = a*x^2*y + b*y^2
    gx = 2 * a * x0 * y0
    gy = a * (x0 * x0) + 2 * b * y0
    prompt = f"Sea $f(x, y) = {a}x^2 y + {b}y^2$. Calcule el vector gradiente $\\nabla f({x0}, {y0})$."
    correct = f"$({gx},\\; {gy})^T$"
    wrongs = [
        f"$({gy},\\; {gx})^T$",
        f"$({a * x0 * y0},\\; {b * y0})^T$",
        f"${gx + gy}$",
    ]
    hint = f"Calcula $\\frac{{\\partial f}}{{\\partial x}} = {2*a}xy$ y $\\frac{{\\partial f}}{{\\partial y}} = {a}x^2 + {2*b}y$, y evalúa en $({x0}, {y0})$."
    explanation = (
        f"Las derivadas parciales son $f_x = {2*a}xy$ y $f_y = {a}x^2 + {2*b}y$. "
        f"En $({x0}, {y0})$: $f_x({x0},{y0}) = {2*a}({x0})({y0}) = {gx}$ y $f_y({x0},{y0}) = {a}({x0}^2) + {2*b}({y0}) = {gy}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_lagrange_linear_sphere():
    a, b = random.choice([(3, 4), (5, 12), (6, 8), (8, 15)])
    norm = int(math.isqrt(a * a + b * b))
    r = random.randint(1, 3)
    ans = norm * r
    prompt = f"Usando Multiplicadores de Lagrange (o Cauchy-Schwarz), ¿cuál es el valor máximo de $f(x, y) = {a}x + {b}y$ sujeto a $x^2 + y^2 = {r*r}$?"
    correct = f"${ans}$"
    wrongs = [
        f"${(a + b) * r}$",
        f"${ans * r}$",
        f"${norm * norm}$",
    ]
    hint = f"El máximo de $c^T x$ sobre $\\|x\\|_2 = R$ se alcanza cuando $x$ es paralelo a $c = ({a}, {b})^T$, y vale $\\|c\\|_2 \\cdot R$."
    explanation = (
        f"Por Lagrange o Cauchy-Schwarz, $\\max_{{x^2+y^2={r}^2}} ({a}x + {b}y) = \\sqrt{{{a}^2 + {b}^2}} \\cdot {r} = {norm} \\cdot {r} = {ans}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_svd_singular_values():
    s1 = random.randint(5, 10)
    s2 = random.randint(2, s1 - 1)
    frob_sq = s1 * s1 + s2 * s2
    prompt = (
        f"Una matriz $A$ de rango 2 tiene valores singulares $\\sigma_1 = {s1}$ y $\\sigma_2 = {s2}$. "
        f"¿Cuánto valen su norma espectral $\\|A\\|_2$ y el cuadrado de su norma de Frobenius $\\|A\\|_F^2$?"
    )
    correct = f"$\\|A\\|_2 = {s1},\\; \\|A\\|_F^2 = {frob_sq}$"
    wrongs = [
        f"$\\|A\\|_2 = {s1*s1},\\; \\|A\\|_F^2 = {s1 + s2}$",
        f"$\\|A\\|_2 = {s2},\\; \\|A\\|_F^2 = {frob_sq}$",
        f"$\\|A\\|_2 = {s1 + s2},\\; \\|A\\|_F^2 = {(s1 + s2)**2}$",
    ]
    hint = "Recuerda que $\\|A\\|_2 = \\sigma_1$ y $\\|A\\|_F^2 = \\sum \\sigma_i^2$."
    explanation = f"La norma espectral es el mayor valor singular $\\sigma_1 = {s1}$, y $\\|A\\|_F^2 = \\sigma_1^2 + \\sigma_2^2 = {s1}^2 + {s2}^2 = {frob_sq}$."
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_graph_handshaking():
    n_v = random.randint(6, 12)
    deg_k = random.choice([3, 4])
    # Sin_v o deg_k son impares aseguramos producto par
    if (n_v * deg_k) % 2 != 0:
        n_v += 1
    edges = (n_v * deg_k) // 2
    prompt = f"Si un grafo regular tiene $|V| = {n_v}$ vértices y cada vértice tiene grado {deg_k}, ¿cuántas aristas $|E|$ tiene el grafo?"
    correct = f"${edges}$"
    wrongs = [
        f"${n_v * deg_k}$",
        f"${n_v - 1}$",
        f"${edges + deg_k}$",
    ]
    hint = "Aplica el Lema del Apretón de Manos: $\\sum_{v \\in V} \\deg(v) = 2|E|$."
    explanation = f"La suma de los grados es ${n_v} \\times {deg_k} = {n_v * deg_k} = 2|E|$, por lo que $|E| = {edges}$."
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_gradient_descent_step():
    x0 = random.choice([2, 4, 6])
    a = random.choice([1, 2, 3])
    # f(x) = a x^2 => f'(x) = 2 a x. Con eta = 1/(4a), x1 = x0 - (1/(4a))*(2a x0) = x0 / 2
    grad0 = 2 * a * x0
    x1 = x0 // 2
    prompt = (
        f"Sea $f(x) = {a if a > 1 else ''}x^2$. Si partimos de $x_0 = {x0}$ y aplicamos un paso de Descenso de Gradiente "
        f"$x_1 = x_0 - \\eta f'(x_0)$ con tasa de aprendizaje $\\eta = \\frac{{1}}{{{4*a}}}$, ¿cuánto vale $x_1$?"
    )
    correct = f"${x1}$"
    wrongs = [
        f"${x0 - grad0}$",
        f"$0$",
        f"${x0 + x1}$",
    ]
    hint = f"Calcula $f'({x0}) = {2*a}({x0}) = {grad0}$ y sustituye en $x_1 = {x0} - \\frac{{1}}{{{4*a}}}({grad0})$."
    explanation = (
        f"Como $f'(x) = {2*a}x$, en $x_0 = {x0}$ el gradiente vale $f'({x0}) = {grad0}$. "
        f"Luego $x_1 = {x0} - \\frac{{1}}{{{4*a}}} \\cdot {grad0} = {x0} - {x0//2} = {x1}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_bayes_theorem():
    vx = random.choice([2, 3, 5])
    vy = random.choice([4, 7, 10])
    a = random.choice([2, 3])
    b = random.choice([2, 3])
    ans = (a * a) * vx + (b * b) * vy
    prompt = (
        f"Sean $X$ e $Y$ variables aleatorias independientes con $\\text{{Var}}(X) = {vx}$ y $\\text{{Var}}(Y) = {vy}$. "
        f"¿Cuánto vale $\\text{{Var}}({a}X - {b}Y + 10)$?"
    )
    correct = f"${ans}$"
    wrongs = [
        f"${(a * a) * vx - (b * b) * vy}$",
        f"${a * vx + b * vy + 10}$",
        f"${a * vx + b * vy}$",
    ]
    hint = "Por independencia $\\text{Cov}(X,Y)=0$ y $\\text{Var}(aX - bY + c) = a^2\\text{Var}(X) + (-b)^2\\text{Var}(Y)$."
    explanation = (
        f"La constante $+10$ no aporta varianza y por independencia: "
        f"$\\text{{Var}}({a}X - {b}Y + 10) = {a}^2({vx}) + (-{b})^2({vy}) = {a*a*vx} + {b*b*vy} = {ans}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_clt_sample_mean():
    sigma = random.choice([12, 15, 20, 30])
    sqrt_n = random.choice([3, 4, 5, 6, 10])
    n = sqrt_n * sqrt_n
    # elegimos pares donde sigma / sqrt_n sea entero o fracción limpia
    if sigma % sqrt_n == 0:
        se_str = f"${sigma // sqrt_n}$"
    else:
        g = math.gcd(sigma, sqrt_n)
        se_str = f"$\\frac{{{sigma // g}}}{{{sqrt_n // g}}}$"
    prompt = (
        f"Se toma una muestra aleatoria simple $X_1, \\dots, X_{{{n}}}$ i.i.d. con media $\\mu = 100$ y desviación estándar poblacional $\\sigma = {sigma}$. "
        f"¿Cuál es el error estándar (desviación estándar) del promedio muestral $\\bar{{X}}_{{{n}}}$?"
    )
    correct = se_str
    wrongs = [
        f"$\\frac{{{sigma}}}{{{n}}}$",
        f"${sigma}$",
        f"$\\frac{{{sigma * sigma}}}{{{sqrt_n}}}$",
    ]
    hint = f"El error estándar de la media muestral es $\\text{{SD}}(\\bar{{X}}_n) = \\frac{{\\sigma}}{{\\sqrt{{n}}}}$. Aquí $\\sqrt{{{n}}} = {sqrt_n}$."
    explanation = f"Como $\\text{{Var}}(\\bar{{X}}_{{{n}}}) = \\frac{{\\sigma^2}}{{n}}$, su desviación estándar es $\\frac{{\\sigma}}{{\\sqrt{{{n}}}}} = \\frac{{{sigma}}}{{{sqrt_n}}} = {se_str.strip('$')}$."
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


GENERATORS = {
    "inequality_abs": gen_inequality_abs,
    "function_composition": gen_function_composition,
    "limit_rational": gen_limit_rational,
    "continuity_param": gen_continuity_param,
    "logic_truth": gen_logic_truth,
    "summation_telescopic": gen_summation_telescopic,
    "vectors_dot_proj": gen_vectors_dot_proj,
    "complex_modulus": gen_complex_modulus,
    "descriptive_stats": gen_descriptive_stats,
    "derivative_chain": gen_derivative_chain,
    "taylor_opt_1d": gen_taylor_opt_1d,
    "definite_integral": gen_definite_integral,
    "matrix_rank_system": gen_matrix_rank_system,
    "rank_nullity": gen_rank_nullity,
    "least_squares_1d": gen_least_squares_1d,
    "eigenvalues_2x2": gen_eigenvalues_2x2,
    "gradient_eval": gen_gradient_eval,
    "lagrange_linear_sphere": gen_lagrange_linear_sphere,
    "svd_singular_values": gen_svd_singular_values,
    "graph_handshaking": gen_graph_handshaking,
    "gradient_descent_step": gen_gradient_descent_step,
    "bayes_theorem": gen_bayes_theorem,
    "clt_sample_mean": gen_clt_sample_mean,
}

PILOT_FAMILY_COUNTS = {
    "inequality_abs": 4,
    "function_composition": 3,
    "limit_rational": 3,
    "continuity_param": 2,
}


def generate_parametric_questions(generator_type, count=2, *, rng=None):
    fn = GENERATORS.get(generator_type, gen_inequality_abs)
    if generator_type in PILOT_FAMILY_COUNTS:
        rng = rng if rng is not None else random
        families = range(PILOT_FAMILY_COUNTS[generator_type])
        out = []
        while len(out) < count:
            batch = rng.sample(families, min(count - len(out), len(families)))
            out.extend(fn(variant=family, rng=rng) for family in batch)
        return out

    out = []
    seen_prompts = set()
    start_v = random.randint(0, 5)
    for idx in range(count * 4):
        v = start_v + idx
        try:
            q = fn(variant=v)
        except TypeError:
            q = fn()
        if q["prompt"] not in seen_prompts:
            seen_prompts.add(q["prompt"])
            out.append(q)
        if len(out) >= count:
            break
    while len(out) < count:
        try:
            out.append(fn(variant=random.randint(0, 2)))
        except TypeError:
            out.append(fn())
    return out


