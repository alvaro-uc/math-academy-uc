# -*- coding: utf-8 -*-
"""
Generador Paramétrico de Problemas Matemáticos (Estilo Math Academy)
Genera ejercicios dinámicos con parámetros aleatorios, distractores plausibles
que capturan errores comunes de Interrogación UC, y solución paso a paso en LaTeX.
"""

import math
import random
import uuid


def _make_mcq(prompt, correct_str, wrong_strs, hint, explanation):
    """Empaqueta una pregunta MCQ barajando las opciones sin duplicados."""
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
    return {
        "id": "gen_" + uuid.uuid4().hex[:8],
        "type": "mcq",
        "is_parametric": True,
        "prompt": prompt,
        "options": options,
        "correct_index": options.index(correct_str),
        "hint": hint,
        "explanation": explanation,
    }


def gen_inequality_abs():
    a = random.choice([2, 3, 4, 5])
    x_center = random.randint(-4, 5)
    r = random.randint(2, 6)
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
        f"$({-high},\\; {-low})$",
    ]
    hint = f"Escribe $-{rad} < {a}x {sign_b} < {rad}$ y despeja $x$."
    explanation = (
        f"Descomponemos como $-{rad} < {a}x {sign_b} < {rad}$. Sumando ${b}$ obtenemos "
        f"${b - rad} < {a}x < {b + rad}$, y dividiendo por ${a} > 0$ resulta $x \\in ({low}, {high})$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_function_composition():
    a = random.randint(2, 5)
    b = random.randint(1, 6)
    c = random.randint(2, 4)
    x0 = random.randint(1, 4)
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
        f"${fx0 * (x0 * x0 - c)}$",
        f"${gfx0 + 2 * c}$",
    ]
    hint = f"Evalúa primero la función interna $u = f({x0})$ y luego calcula $g(u)$."
    explanation = (
        f"Primero calculamos $f({x0}) = {a}({x0}) + {b} = {fx0}$. "
        f"Luego evaluamos $g({fx0}) = ({fx0})^2 - {c} = {fx0*fx0} - {c} = {gfx0}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_limit_rational():
    r1 = random.randint(1, 5)
    r2 = random.choice([i for i in range(-5, 6) if i != r1 and i != -r1])
    # Lim_{x -> r1} (x^2 - (r1+r2)x + r1*r2) / (x - r1) = r1 - r2
    b_coef = -(r1 + r2)
    c_coef = r1 * r2
    val = r1 - r2
    b_str = f"+ {b_coef}x" if b_coef > 0 else (f"- {-b_coef}x" if b_coef < 0 else "")
    c_str = f"+ {c_coef}" if c_coef > 0 else (f"- {-c_coef}" if c_coef < 0 else "")
    prompt = f"Calcule el límite $\\lim_{{x \\to {r1}}} \\frac{{x^2 {b_str} {c_str}}}{{x - {r1}}}$."
    correct = f"${val}$"
    wrongs = [
        f"${r1 + r2}$",
        f"${-val}$",
        "$0$",
        "No existe",
    ]
    hint = f"Factoriza el numerador como $(x - {r1})(x - ({r2}))$ para cancelar la indeterminación $0/0$."
    explanation = (
        f"Factorizando el numerador: $\\frac{{(x - {r1})(x - ({r2}))}}{{x - {r1}}} = x - ({r2})$ para $x \\neq {r1}$. "
        f"Evaluando en $x \\to {r1}$ obtenemos ${r1} - ({r2}) = {val}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_continuity_param():
    x0 = random.randint(1, 3)
    c = random.randint(1, 5)
    # f(x) = x^2 + c for x <= x0, ax + b for x > x0, derivable at x0
    a_val = 2 * x0
    b_val = (x0 * x0 + c) - a_val * x0  # c - x0^2
    prompt = (
        f"Determine $(a, b)$ para que $f(x) = \\begin{{cases}} x^2 + {c} & x \\le {x0} \\\\ ax + b & x > {x0} \\end{{cases}}$ "
        f"sea continua y derivable en $x = {x0}$."
    )
    correct = f"$a = {a_val},\\; b = {b_val}$"
    wrongs = [
        f"$a = {a_val},\\; b = {x0 * x0 + c}$",
        f"$a = {x0},\\; b = {c}$",
        f"$a = {a_val},\\; b = {-b_val if b_val != 0 else 2}$",
    ]
    hint = f"Iguala primero las derivadas laterales en $x = {x0}$ para hallar $a = 2({x0})$, y luego iguala los límites laterales para hallar $b$."
    explanation = (
        f"Para derivabilidad en $x={x0}$ necesitamos $f'_-({x0}) = 2({x0}) = {a_val} = a$. "
        f"Por continuidad en $x={x0}$: ${x0}^2 + {c} = {a_val}({x0}) + b \\implies {x0*x0+c} = {a_val*x0} + b \\implies b = {b_val}$."
    )
    return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_logic_truth():
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
    ]
    p, c, w, h, e = random.choice(variants)
    return _make_mcq(p, c, w, h, e)


def gen_summation_telescopic():
    n = random.choice([10, 15, 20, 30])
    c = random.randint(1, 5)
    # sum_{k=1}^n (2k + c) = n(n+1) + c*n
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


def gen_vectors_dot_proj():
    u1, u2, u3 = random.randint(1, 4), random.randint(-3, 3), random.randint(1, 4)
    v1, v2 = random.randint(1, 3), random.randint(1, 3)
    # queremos u . v = dot_val
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


def gen_complex_modulus():
    a, b = random.choice([(3, 4), (5, 12), (1, 1), (2, 2)])
    n = random.choice([2, 3, 4])
    mod_sq = a * a + b * b
    # si a=3,b=4 -> |z|=5, |z^n| = 5^n
    if a in (3, 5):
        r = int(math.isqrt(mod_sq))
        ans = r ** n
        prompt = f"Sea $z = {a} - {b}i \\in \\mathbb{{C}}$. ¿Cuál es el módulo $|z^{n}|$?"
        correct = f"${ans}$"
        wrongs = [f"${r * n}$", f"${mod_sq ** n}$", f"${(a + b) ** n}$"]
        hint = f"Usa la propiedad multiplicativa del módulo: $|z^{n}| = |z|^{n}$ con $|z| = \\sqrt{{{a}^2 + (-{b})^2}}$."
        explanation = f"Como $|z| = \\sqrt{{{a}^2 + (-{b})^2}} = \\sqrt{{{mod_sq}}} = {r}$, entonces $|z^{n}| = |z|^{n} = {r}^{n} = {ans}$."
        return _make_mcq(prompt, correct, wrongs, hint, explanation)
    else:
        ans = mod_sq ** (n // 2) if n % 2 == 0 else f"{mod_sq}\\sqrt{{{mod_sq}}}"
        prompt = f"Sea $z = {a} + {b}i$. ¿Cuánto vale $|z|^2 = z \\bar{{z}}$?"
        correct = f"${mod_sq}$"
        wrongs = [f"${a + b}$", f"$0$", f"${a*a - b*b}$"]
        hint = "Recuerda que $(a + bi)(a - bi) = a^2 + b^2$."
        explanation = f"$z\\bar{{z}} = {a}^2 + {b}^2 = {mod_sq}$."
        return _make_mcq(prompt, correct, wrongs, hint, explanation)


def gen_descriptive_stats():
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


def generate_parametric_questions(generator_type, count=2):
    fn = GENERATORS.get(generator_type, gen_inequality_abs)
    out = []
    seen_prompts = set()
    for _ in range(count * 4):
        q = fn()
        if q["prompt"] not in seen_prompts:
            seen_prompts.add(q["prompt"])
            out.append(q)
        if len(out) >= count:
            break
    while len(out) < count:
        out.append(fn())
    return out
