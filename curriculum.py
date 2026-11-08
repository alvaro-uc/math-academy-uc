# -*- coding: utf-8 -*-
"""
Currículum y Grafo de Conocimiento (DAG + Pesos FIRe)
Licenciatura en Ingeniería en Ciencia de Datos — Pontificia Universidad Católica de Chile (UC)
"""

COURSES = [
    {
        "id": "IC",
        "code": "MAT1600 / IMC",
        "name": "Introducción al Cálculo",
        "semester": 1,
        "domain": "calculo",
        "color": "#0891b2",
        "description": "Fundamentos de números reales, desigualdades, funciones, límites, continuidad e introducción a la derivada.",
    },
    {
        "id": "IAG",
        "code": "MAT1200 / IMC",
        "name": "Introducción a Álgebra y Geometría",
        "semester": 1,
        "domain": "algebra",
        "color": "#4f46e5",
        "description": "Lógica, demostraciones, inducción, sumatorias, geometría vectorial en R^n, complejos y polinomios.",
    },
    {
        "id": "TME",
        "code": "EYP1010 / IMC",
        "name": "Taller de Matemáticas y Estadística",
        "semester": 1,
        "domain": "prob_est",
        "color": "#0d9488",
        "description": "Combinatoria fundamental, estadística descriptiva, cuantiles, dispersión y análisis exploratorio cuantitativo.",
    },
    {
        "id": "C1",
        "code": "MAT1610",
        "name": "Cálculo I",
        "semester": 2,
        "domain": "calculo",
        "color": "#0284c7",
        "description": "Cálculo diferencial (regla de la cadena, TVM, Taylor, optimización) y cálculo integral (Riemann, TFC, técnicas e impropias).",
    },
    {
        "id": "ALCD",
        "code": "IMC / MAT",
        "name": "Álgebra Lineal para Ciencia de Datos",
        "semester": 2,
        "domain": "algebra",
        "color": "#6366f1",
        "description": "Sistemas lineales, subespacios, independencia lineal, ortogonalidad, mínimos cuadrados y valores propios.",
    },
    {
        "id": "CCD",
        "code": "IMC Sem 3",
        "name": "Cálculo para Ciencia de Datos",
        "semester": 3,
        "domain": "calculo",
        "color": "#0369a1",
        "description": "Cálculo multivariable: gradiente, regla de la cadena matricial, Hessiana, Lagrange e integrales múltiples.",
    },
    {
        "id": "ALAM",
        "code": "IMC Sem 3",
        "name": "Álgebra Lineal Avanzada y Modelamiento",
        "semester": 3,
        "domain": "algebra",
        "color": "#4338ca",
        "description": "Matrices definidas positivas, descomposición en valores singulares (SVD), aproximación de bajo rango (PCA) y condicionamiento.",
    },
    {
        "id": "MD",
        "code": "IIC1253",
        "name": "Matemáticas Discretas",
        "semester": 3,
        "domain": "discretas_opt",
        "color": "#d97706",
        "description": "Relaciones de recurrencia, órdenes asintóticos (Big-O), grafos, árboles y estructuras discretas para algoritmos.",
    },
    {
        "id": "OCD",
        "code": "IMC Sem 4",
        "name": "Optimización para Ciencia de Datos",
        "semester": 4,
        "domain": "discretas_opt",
        "color": "#ea580c",
        "description": "Análisis convexo, descenso de gradiente, tasas de convergencia y condiciones de optimalidad KKT.",
    },
    {
        "id": "MP",
        "code": "EYP Sem 4",
        "name": "Modelos Probabilísticos",
        "semester": 4,
        "domain": "prob_est",
        "color": "#059669",
        "description": "Probabilidad condicional, Bayes, variables y vectores aleatorios, esperanza condicional y teoremas límite (LGN, TCL).",
    },
]

TOPICS = [
    # ==========================================
    # SEMESTRE 1: INTRODUCCIÓN AL CÁLCULO (IC)
    # ==========================================
    {
        "id": "ic_desigualdades",
        "title": "Desigualdades, Valor Absoluto y Cotas en ℝ",
        "course_id": "IC",
        "semester": 1,
        "domain": "calculo",
        "xp": 10,
        "estimated_mins": 8,
        "prereqs": [],
        "encompasses": {},
        "generator_type": "inequality_abs",
        "theory": (
            "En $\\mathbb{R}$, el **valor absoluto** mide distancia al origen y verifica la **desigualdad triangular**:\n"
            "$$|x + y| \\le |x| + |y| \\quad \\text{y} \\quad \\big||x| - |y|\\big| \\le |x - y|$$\n"
            "Para resolver $|f(x)| < a$ con $a > 0$, usamos la equivalencia directa $-a < f(x) < a$. "
            "En desigualdades racionales como $\\frac{P(x)}{Q(x)} \\ge 0$, **nunca multipliques cruzado** por $Q(x)$ sin conocer su signo: "
            "pasa todo a un lado, factoriza y analiza signos en una tabla de puntos críticos."
        ),
        "ds_connection": (
            "Las normas $\\ell_1$ (Lasso, $|w|$) y $\\ell_2$ (Ridge, $w^2$) y las cotas de error de generalización "
            "en Machine Learning dependen directamente de la desigualdad triangular y de acotar expresiones con valor absoluto."
        ),
        "uc_exam_tip": (
            "En la I1 de Introducción al Cálculo es clásico pedir el conjunto solución de $\\frac{|x-a|}{x-b} \\le c$ o hallar "
            "supremo e ínfimo de un conjunto acotado. Verifica siempre excluir las raíces del denominador."
        ),
        "worked_example": {
            "problem": "Resuelva en $\\mathbb{R}$ la inecuación $|2x - 5| < 7$ y exprese la solución como intervalo.",
            "steps": [
                "Aplicamos la propiedad $|u| < a \\iff -a < u < a$ para $a = 7 > 0$:\n$$-7 < 2x - 5 < 7$$",
                "Sumamos $5$ en los tres miembros de la desigualdad:\n$$-2 < 2x < 12$$",
                "Dividimos por $2 > 0$ (el sentido de la desigualdad se mantiene):\n$$-1 < x < 6$$",
            ],
            "final_answer": "$x \\in (-1, 6)$",
        },
        "questions": [
            {
                "id": "q_ic_des_1",
                "type": "mcq",
                "prompt": "¿Cuál es el conjunto solución de la inecuación $\\frac{x - 3}{x + 1} \\le 0$?",
                "options": [
                    "$(-1, 3]$",
                    "$[-1, 3]$",
                    "$(-\\infty, -1) \\cup [3, \\infty)$",
                    "$(-1, 3)$",
                ],
                "correct_index": 0,
                "hint": "Identifica los puntos críticos $x = 3$ y $x = -1$. Recuerda que el denominador $x+1$ no puede anularse.",
                "explanation": "Los signos de $(x-3)$ y $(x+1)$ son opuestos en $[-1, 3]$. Como $x \\neq -1$ para no dividir por cero y $x=3$ anula el numerador, la solución es $(-1, 3]$.",
            },
            {
                "id": "q_ic_des_2",
                "type": "mcq",
                "prompt": "Sea $A = \\left\\{ 2 - \\frac{3}{n} : n \\in \\mathbb{N}_{\\ge 1} \\right\\}$. ¿Cuáles son $\\inf(A)$ y $\\sup(A)$ respectivamente?",
                "options": [
                    "$\\inf(A) = -1,\\; \\sup(A) = 2$",
                    "$\\inf(A) = 0,\\; \\sup(A) = 2$",
                    "$\\inf(A) = -1,\\; \\sup(A) = 5$",
                    "No tiene ínfimo y $\\sup(A) = 2$",
                ],
                "correct_index": 0,
                "hint": "Evalúa en $n=1$ y analiza el comportamiento cuando $n \\to \\infty$.",
                "explanation": "La sucesión $a_n = 2 - 3/n$ es estrictamente creciente. Su mínimo (e ínfimo) se alcanza en $n=1$ con $2 - 3 = -1$, y cuando $n \\to \\infty$, $a_n \\to 2^-$, por lo que $\\sup(A) = 2$.",
            },
        ],
    },
    {
        "id": "ic_funciones",
        "title": "Funciones Reales, Inyectividad y Composición",
        "course_id": "IC",
        "semester": 1,
        "domain": "calculo",
        "xp": 10,
        "estimated_mins": 9,
        "prereqs": ["ic_desigualdades"],
        "encompasses": {"ic_desigualdades": 0.5},
        "generator_type": "function_composition",
        "theory": (
            "Una función $f: A \\to B$ es **inyectiva** (1-a-1) si $f(x_1) = f(x_2) \\implies x_1 = x_2$, y **sobreyectiva** "
            "si $\\text{Rec}(f) = B$. Solo las funciones **biyectivas** admiten inversa $f^{-1}: B \\to A$.\n\n"
            "En la composición $(g \\circ f)(x) = g(f(x))$, el dominio exige dos condiciones simultáneas:\n"
            "$$\\text{Dom}(g \\circ f) = \\{x \\in \\text{Dom}(f) : f(x) \\in \\text{Dom}(g)\\}$$"
        ),
        "ds_connection": (
            "Una red neuronal profunda de $L$ capas no es más que una composición de funciones "
            "$\\hat{y} = (f_L \\circ f_{L-1} \\circ \\dots \\circ f_1)(x)$, y las transformaciones invertibles (Normalizing Flows, Box-Cox) requieren biyectividad."
        ),
        "uc_exam_tip": (
            "Cuando te pidan restringir el dominio de una cuadrática $f(x) = ax^2 + bx + c$ para hacerla biyectiva, "
            "completa el cuadrado primero: $a(x - h)^2 + k$. El vértice $x = h$ divide las dos ramas monótonas."
        ),
        "worked_example": {
            "problem": "Sea $f(x) = x^2 - 4x + 7$ definida en $[2, +\\infty)$. Encuentre su recorrido y la fórmula de $f^{-1}(y)$.",
            "steps": [
                "Completamos el cuadrado perfecto:\n$$f(x) = (x - 2)^2 - 4 + 7 = (x - 2)^2 + 3$$",
                "Como $x \\ge 2$, tenemos $(x-2)^2 \\ge 0$, por lo que $y = f(x) \\ge 3$. El recorrido es $[3, +\\infty)$.",
                "Despejamos $x$ en términos de $y$: $(x - 2)^2 = y - 3 \\implies x - 2 = +\\sqrt{y - 3}$ (tomamos la raíz positiva pues $x \\ge 2$).",
            ],
            "final_answer": "$f^{-1}(y) = 2 + \\sqrt{y - 3}$ con dominio $[3, +\\infty)$",
        },
        "questions": [
            {
                "id": "q_ic_fun_1",
                "type": "mcq",
                "prompt": "Si $f(x) = \\sqrt{x - 2}$ y $g(x) = \\ln(5 - x)$, ¿cuál es el dominio máximo de $(g \\circ f)(x) = g(f(x))$?",
                "options": [
                    "$[2, 27)$",
                    "$[2, 5)$",
                    "$(2, 27]$",
                    "$[0, 25)$",
                ],
                "correct_index": 0,
                "hint": "Necesitas $x \\in \\text{Dom}(f)$ ($x \\ge 2$) y además $f(x) \\in \\text{Dom}(g)$, es decir $5 - \\sqrt{x-2} > 0$.",
                "explanation": "Requerimos $x - 2 \\ge 0 \\implies x \\ge 2$ y además $5 - \\sqrt{x-2} > 0 \\implies \\sqrt{x-2} < 5 \\implies x - 2 < 25 \\implies x < 27$. Intersectando: $[2, 27)$.",
            }
        ],
    },
    {
        "id": "ic_limites",
        "title": "Límites de Funciones y Límites Notables",
        "course_id": "IC",
        "semester": 1,
        "domain": "calculo",
        "xp": 12,
        "estimated_mins": 10,
        "prereqs": ["ic_funciones"],
        "encompasses": {"ic_funciones": 0.5, "ic_desigualdades": 0.4},
        "generator_type": "limit_rational",
        "theory": (
            "Decimos que $\\lim_{x \\to a} f(x) = L$ si para todo $\\varepsilon > 0$ existe $\\delta > 0$ tal que "
            "$0 < |x - a| < \\delta \\implies |f(x) - L| < \\varepsilon$.\n\n"
            "**Herramientas clave para formas indeterminadas $0/0$:**\n"
            "1. Factorización o racionalización (multiplicar por el conjugado $\\sqrt{A} \\pm \\sqrt{B}$).\n"
            "2. **Teorema del Sándwich (Acotamiento)**: si $g(x) \\le f(x) \\le h(x)$ y $\\lim g = \\lim h = L$, entonces $\\lim f = L$.\n"
            "3. Límites notables: $\\lim_{u \\to 0} \\frac{\\sin(u)}{u} = 1$, $\\lim_{u \\to 0} \\frac{1 - \\cos(u)}{u^2} = \\frac{1}{2}$, $\\lim_{u \\to 0} \\frac{e^u - 1}{u} = 1$."
        ),
        "ds_connection": (
            "Las tasas de aprendizaje infinitesimales (tiempo continuo en SDEs/Diffusion Models) y las aproximaciones locales "
            "de funciones de pérdida dependen del comportamiento asintótico y de límites notables."
        ),
        "uc_exam_tip": (
            "En Introducción al Cálculo **no está permitido usar L'Hôpital** en las interrogaciones (se ve recién en Cálculo I). "
            "Domina el cambio de variable $u = x - a$ para llevar límites en $x \\to a$ a límites en $u \\to 0$."
        ),
        "worked_example": {
            "problem": "Calcule sin usar regla de L'Hôpital: $\\lim_{x \\to 0} \\frac{\\sqrt{1 + 3x} - 1}{x}$.",
            "steps": [
                "Multiplicamos numerador y denominador por el conjugado $(\\sqrt{1+3x} + 1)$:\n$$\\frac{(\\sqrt{1+3x}-1)(\\sqrt{1+3x}+1)}{x(\\sqrt{1+3x}+1)} = \\frac{(1+3x) - 1}{x(\\sqrt{1+3x}+1)}$$",
                "Simplificamos el factor $x \\neq 0$:\n$$\\frac{3x}{x(\\sqrt{1+3x}+1)} = \\frac{3}{\\sqrt{1+3x}+1}$$",
                "Evaluamos el límite cuando $x \\to 0$: $\\frac{3}{\\sqrt{1} + 1} = \\frac{3}{2}$.",
            ],
            "final_answer": "$\\frac{3}{2}$",
        },
        "questions": [
            {
                "id": "q_ic_lim_1",
                "type": "mcq",
                "prompt": "¿Cuál es el valor de $\\lim_{x \\to 0} \\frac{\\sin(4x)}{\\sin(2x)}$?",
                "options": ["$2$", "$4$", "$1/2$", "$0$"],
                "correct_index": 0,
                "hint": "Usa $\\frac{\\sin(kx)}{kx} \\to 1$ o la identidad del ángulo doble $\\sin(4x) = 2\\sin(2x)\\cos(2x)$.",
                "explanation": "Como $\\sin(4x) = 2\\sin(2x)\\cos(2x)$, el cociente se simplifica a $2\\cos(2x)$, que tiende a $2\\cos(0) = 2$ cuando $x \\to 0$.",
            }
        ],
    },
    {
        "id": "ic_continuidad_derivada",
        "title": "Continuidad, TVI e Introducción a la Derivada",
        "course_id": "IC",
        "semester": 1,
        "domain": "calculo",
        "xp": 12,
        "estimated_mins": 10,
        "prereqs": ["ic_limites"],
        "encompasses": {"ic_limites": 0.75, "ic_funciones": 0.4},
        "generator_type": "continuity_param",
        "theory": (
            "$f$ es **continua en $a$** si $\\lim_{x \\to a^-} f(x) = \\lim_{x \\to a^+} f(x) = f(a)$.\n"
            "- **Teorema del Valor Intermedio (TVI / Bolzano)**: Si $f$ es continua en $[a,b]$ y $f(a)\\cdot f(b) < 0$, existe al menos una raíz $c \\in (a,b)$ tal que $f(c) = 0$.\n"
            "- **Derivada por definición**:\n"
            "$$f'(a) = \\lim_{h \\to 0} \\frac{f(a+h) - f(a)}{h} = \\lim_{x \\to a} \\frac{f(x) - f(a)}{x - a}$$\n"
            "Toda función derivable en $a$ es continua en $a$, pero **el recíproco es falso** (ej. $f(x) = |x|$ en $x = 0$)."
        ),
        "ds_connection": (
            "Las funciones de activación como ReLU $\\max(0, x)$ son continuas en todo $\\mathbb{R}$ pero no diferenciables en $x=0$, "
            "lo que motiva el uso de subgradientes en el entrenamiento de redes neuronales."
        ),
        "uc_exam_tip": (
            "En funciones definidas por tramos en $x = x_0$: para pedir que sea **derivable** en $x_0$, primero exige **continuidad** "
            "(igualando límites laterales) y recién después iguala las derivadas laterales."
        ),
        "worked_example": {
            "problem": "Determine $a, b \\in \\mathbb{R}$ para que $f(x) = \\begin{cases} x^2 + 1 & x \\le 1 \\\\ ax + b & x > 1 \\end{cases}$ sea derivable en $x = 1$.",
            "steps": [
                "Condición 1 (Continuidad en $x=1$): $\\lim_{x \\to 1^-} (x^2+1) = 2$ y $\\lim_{x \\to 1^+} (ax+b) = a+b$, luego $a + b = 2$.",
                "Condición 2 (Derivadas laterales iguales en $x=1$): $f'_{-}(1) = \\left.2x\\right|_{x=1} = 2$ y $f'_{+}(1) = a$, por lo tanto $a = 2$.",
                "Sustituyendo $a = 2$ en $a + b = 2$, obtenemos $b = 0$.",
            ],
            "final_answer": "$a = 2,\\; b = 0$",
        },
        "questions": [
            {
                "id": "q_ic_cont_1",
                "type": "mcq",
                "prompt": "Sea $f(x) = x^3 + x - 3$. Por el Teorema de Bolzano (TVI), ¿en cuál de estos intervalos se garantiza que existe una solución real de $f(x) = 0$?",
                "options": ["$(1, 2)$", "$(0, 1)$", "$(-1, 0)$", "$(2, 3)$"],
                "correct_index": 0,
                "hint": "Evalúa el signo de $f$ en los extremos de cada intervalo.",
                "explanation": "Como $f$ es polinomial (continua en $\\mathbb{R}$), $f(1) = 1 + 1 - 3 = -1 < 0$ y $f(2) = 8 + 2 - 3 = 7 > 0$. Al cambiar de signo, Bolzano garantiza una raíz en $(1,2)$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 1: INTRODUCCIÓN A ÁLGEBRA Y GEOMETRÍA (IAG)
    # ==========================================
    {
        "id": "iag_logica_conjuntos",
        "title": "Lógica Proposicional, Cuantificadores y Demostraciones",
        "course_id": "IAG",
        "semester": 1,
        "domain": "algebra",
        "xp": 10,
        "estimated_mins": 8,
        "prereqs": [],
        "encompasses": {},
        "generator_type": "logic_truth",
        "theory": (
            "La implicancia $p \\implies q$ es lógicamente equivalente a:\n"
            "1. **Forma disyuntiva**: $\\neg p \\lor q$\n"
            "2. **Contrarrecíproca**: $\\neg q \\implies \\neg p$\n\n"
            "La **negación de una implicancia** es $\\neg(p \\implies q) \\equiv p \\land \\neg q$ (¡no es otra implicancia!).\n"
            "Para cuantificadores: $\\neg(\\forall x\\, P(x)) \\equiv \\exists x\\, \\neg P(x)$ y $\\neg(\\exists x\\, P(x)) \\equiv \\forall x\\, \\neg P(x)$."
        ),
        "ds_connection": (
            "Las consultas relacionales en SQL, los filtros booleanos vectorizados en Pandas/Polars y la verificación formal de algoritmos "
            "son aplicaciones directas del álgebra de Boole y las leyes de De Morgan."
        ),
        "uc_exam_tip": (
            "Cuando te pidan negar la definición $\\varepsilon$-$\\delta$ de límite ($\"\\forall \\varepsilon > 0, \\exists \\delta > 0, \\forall x : P \\implies Q\"$), "
            "invierte cada cuantificador y transforma el $P \\implies Q$ final en $P \\land \\neg Q$."
        ),
        "worked_example": {
            "problem": "Niegue formalmente la proposición: $\\forall x \\in \\mathbb{R},\\; (x > 0 \\implies \\exists y \\in \\mathbb{R},\\; y^2 = x)$.",
            "steps": [
                "Cambiamos el cuantificador universal $\\forall x$ por existencial $\\exists x$ y negamos el predicado interno.",
                "Usamos $\\neg(P \\implies Q) \\equiv P \\land \\neg Q$, manteniendo $x > 0$ verdadero y negando la conclusión.",
                "Negamos $\\exists y \\in \\mathbb{R},\\; y^2 = x$ obteniendo $\\forall y \\in \\mathbb{R},\\; y^2 \\neq x$.",
            ],
            "final_answer": "$\\exists x \\in \\mathbb{R},\\; (x > 0 \\;\\land\\; \\forall y \\in \\mathbb{R},\\; y^2 \\neq x)$",
        },
        "questions": [
            {
                "id": "q_iag_log_1",
                "type": "mcq",
                "prompt": "¿Cuál de las siguientes proposiciones es lógicamente equivalente a la contrarrecíproca de $(p \\land q) \\implies r$?",
                "options": [
                    "$\\neg r \\implies (\\neg p \\lor \\neg q)$",
                    "$\\neg r \\implies (\\neg p \\land \\neg q)$",
                    "$r \\implies (p \\land q)$",
                    "$(\\neg p \\lor \\neg q) \\implies \\neg r$",
                ],
                "correct_index": 0,
                "hint": "La contrarrecíproca de $A \\implies B$ es $\\neg B \\implies \\neg A$, y luego aplica De Morgan a $\\neg(p \\land q)$.",
                "explanation": "La contrarrecíproca es $\\neg r \\implies \\neg(p \\land q)$, y por ley de De Morgan $\\neg(p \\land q) \\equiv \\neg p \\lor \\neg q$.",
            }
        ],
    },
    {
        "id": "iag_induccion_sumatorias",
        "title": "Inducción Matemática, Sumatorias y Binomio de Newton",
        "course_id": "IAG",
        "semester": 1,
        "domain": "algebra",
        "xp": 12,
        "estimated_mins": 10,
        "prereqs": ["iag_logica_conjuntos"],
        "encompasses": {"iag_logica_conjuntos": 0.5},
        "generator_type": "summation_telescopic",
        "theory": (
            "**Sumatorias fundamentales:**\n"
            "$$\\sum_{k=1}^n k = \\frac{n(n+1)}{2}, \\quad \\sum_{k=1}^n k^2 = \\frac{n(n+1)(2n+1)}{6}, \\quad \\sum_{k=0}^n r^k = \\frac{r^{n+1}-1}{r-1}\\;(r\\neq 1)$$\n"
            "**Propiedad Telescópica:** $\\sum_{k=1}^n (a_k - a_{k-1}) = a_n - a_0$.\n"
            "**Teorema del Binomio de Newton:** $(a+b)^n = \\sum_{k=0}^n \\binom{n}{k} a^{n-k} b^k$."
        ),
        "ds_connection": (
            "El análisis de complejidad temporal de algoritmos anidados (ej. número de comparaciones u operaciones de punto flotante FLOPs "
            "en descomposición LU o entrenamiento por épocas) se reduce a calcular sumatorias cerradas."
        ),
        "uc_exam_tip": (
            "En sumatorias racionales del tipo $\\sum_{k=1}^n \\frac{1}{(k+a)(k+a+1)}$, usa fracciones parciales "
            "$\\frac{1}{k+a} - \\frac{1}{k+a+1}$ para aplicar la propiedad telescópica en dos líneas."
        ),
        "worked_example": {
            "problem": "Encuentre el término independiente de $x$ en el desarrollo de $\\left(2x^2 - \\frac{1}{x}\\right)^9$.",
            "steps": [
                "El término general $T_k$ ($0 \\le k \\le 9$) es:\n$$T_k = \\binom{9}{k} (2x^2)^{9-k} (-x^{-1})^k = \\binom{9}{k} 2^{9-k} (-1)^k x^{18 - 2k - k}$$",
                "Buscamos que el exponente de $x$ sea $0$: $18 - 3k = 0 \\implies k = 6$.",
                "Evaluamos el coeficiente en $k=6$: $\\binom{9}{6} 2^{3} (-1)^6 = 84 \\cdot 8 \\cdot 1 = 672$.",
            ],
            "final_answer": "$672$",
        },
        "questions": [
            {
                "id": "q_iag_sum_1",
                "type": "mcq",
                "prompt": "¿Cuál es el valor exacto de la suma telescópica $\\sum_{k=1}^{99} \\frac{1}{k(k+1)}$?",
                "options": ["$99/100$", "$100/99$", "$98/99$", "$1$"],
                "correct_index": 0,
                "hint": "Escribe $\\frac{1}{k(k+1)} = \\frac{1}{k} - \\frac{1}{k+1}$.",
                "explanation": "Al expandir $\\sum_{k=1}^{99} \\left(\\frac{1}{k} - \\frac{1}{k+1}\\right)$, todos los términos intermedios se cancelan quedando $1 - \\frac{1}{100} = \\frac{99}{100}$.",
            }
        ],
    },
    {
        "id": "iag_vectores_geometria",
        "title": "Vectores en ℝⁿ, Producto Punto, Rectas y Planos",
        "course_id": "IAG",
        "semester": 1,
        "domain": "algebra",
        "xp": 12,
        "estimated_mins": 10,
        "prereqs": ["iag_logica_conjuntos"],
        "encompasses": {"iag_logica_conjuntos": 0.4},
        "generator_type": "vectors_dot_proj",
        "theory": (
            "Dados $u, v \\in \\mathbb{R}^n$, su **producto punto** es $u \\cdot v = \\sum_{i=1}^n u_i v_i = \\|u\\|\\,\\|v\\|\\cos\\theta$.\n"
            "- **Ortogonalidad**: $u \\perp v \\iff u \\cdot v = 0$.\n"
            "- **Proyección ortogonal** de $u$ sobre $v \\neq 0$:\n"
            "$$\\text{proy}_v(u) = \\left(\\frac{u \\cdot v}{\\|v\\|^2}\\right) v$$\n"
            "- Un **hiperplano** con vector normal $n \\neq 0$ que pasa por $p_0$ tiene ecuación $n \\cdot (x - p_0) = 0$."
        ),
        "ds_connection": (
            "La **similitud coseno** $\\cos\\theta = \\frac{u \\cdot v}{\\|u\\|\\,\\|v\\|}$ es la métrica estándar en NLP y sistemas recomendadores para comparar embeddings, "
            "y el clasificador SVM busca el hiperplano $w \\cdot x + b = 0$ de máximo margen."
        ),
        "uc_exam_tip": (
            "La distancia de un punto $P$ a un plano $ax + by + cz + d = 0$ se calcula rápido proyectando sobre el vector normal: "
            "$d(P, \\Pi) = \\frac{|a x_P + b y_P + c z_P + d|}{\\sqrt{a^2+b^2+c^2}}$."
        ),
        "worked_example": {
            "problem": "Dados $u = (2, -1, 2)$ y $v = (1, 2, 2)$ en $\\mathbb{R}^3$, calcule la proyección ortogonal $\\text{proy}_v(u)$.",
            "steps": [
                "Calculamos el producto punto: $u \\cdot v = 2(1) + (-1)(2) + 2(2) = 2 - 2 + 4 = 4$.",
                "Calculamos la norma al cuadrado de $v$: $\\|v\\|^2 = 1^2 + 2^2 + 2^2 = 9$.",
                "Aplicamos la fórmula $\\text{proy}_v(u) = \\frac{u \\cdot v}{\\|v\\|^2} v = \\frac{4}{9}(1, 2, 2)$.",
            ],
            "final_answer": "$\\left(\\frac{4}{9}, \\frac{8}{9}, \\frac{8}{9}\\right)$",
        },
        "questions": [
            {
                "id": "q_iag_vec_1",
                "type": "mcq",
                "prompt": "¿Para qué valor de $k \\in \\mathbb{R}$ los vectores $u = (k, 3, -1)$ y $v = (2, -k, 4)$ son ortogonales?",
                "options": ["$k = -4$", "$k = 4$", "$k = 0$", "Para todo $k \\in \\mathbb{R}$"],
                "correct_index": 0,
                "hint": "Impón la condición $u \\cdot v = 0$.",
                "explanation": "Calculamos $u \\cdot v = 2k - 3k - 4 = -k - 4 = 0 \\implies k = -4$.",
            }
        ],
    },
    {
        "id": "iag_complejos_polinomios",
        "title": "Números Complejos, De Moivre y Raíces de Polinomios",
        "course_id": "IAG",
        "semester": 1,
        "domain": "algebra",
        "xp": 11,
        "estimated_mins": 9,
        "prereqs": ["iag_induccion_sumatorias"],
        "encompasses": {"iag_induccion_sumatorias": 0.5},
        "generator_type": "complex_modulus",
        "theory": (
            "Todo complejo $z = a + bi$ se escribe en **forma polar/exponencial** como $z = r e^{i\\theta} = r(\\cos\\theta + i\\sin\\theta)$ "
            "con módulo $r = |z| = \\sqrt{a^2+b^2}$.\n"
            "- **Fórmula de De Moivre**: $(r e^{i\\theta})^n = r^n e^{in\\theta}$.\n"
            "- **Polinomios**: Por el Teorema del Resto, el resto de dividir $P(x)$ por $(x-c)$ es $P(c)$. "
            "Si $P(x) \\in \\mathbb{R}[x]$ y $z_0 \\in \\mathbb{C}$ es raíz, su conjugado $\\overline{z_0}$ también es raíz."
        ),
        "ds_connection": (
            "Las raíces de la unidad $e^{-2\\pi i k / N}$ son la base de la **Transformada Rápida de Fourier (FFT)** para procesamiento de señales y series de tiempo, "
            "y los valores propios complejos gobiernan la estabilidad de sistemas dinámicos y cadenas de Markov."
        ),
        "uc_exam_tip": (
            "Para calcular potencias altas como $(1 + i\\sqrt{3})^{30}$, **jamás** expandas con el binomio: "
            "pasa a forma polar $2 e^{i\\pi/3}$ y aplica De Moivre directamente."
        ),
        "worked_example": {
            "problem": "Si $P(x) = x^3 - 4x^2 + 6x - 4$ tiene a $z_1 = 1 + i$ como raíz, halle todas las raíces de $P(x)$.",
            "steps": [
                "Como $P(x)$ tiene coeficientes reales, el conjugado $z_2 = 1 - i$ también es raíz de $P(x)$.",
                "Por las relaciones de Vieta (o dividiendo por $(x-z_1)(x-z_2) = x^2 - 2x + 2$), la suma de las tres raíces es $z_1 + z_2 + z_3 = 4$.",
                "Como $z_1 + z_2 = 2$, deducimos que la tercera raíz real es $z_3 = 4 - 2 = 2$.",
            ],
            "final_answer": "$\\{1 + i,\\; 1 - i,\\; 2\\}$",
        },
        "questions": [
            {
                "id": "q_iag_comp_1",
                "type": "mcq",
                "prompt": "¿Cuál es el valor de $(1 + i)^8$?",
                "options": ["$16$", "$-16$", "$16i$", "$8$"],
                "correct_index": 0,
                "hint": "Escribe $1+i = \\sqrt{2} e^{i\\pi/4}$ y eleva a la octava potencia.",
                "explanation": "Como $|1+i| = \\sqrt{2}$ y $\\arg(1+i) = \\pi/4$, por De Moivre $(1+i)^8 = (\\sqrt{2})^8 e^{i\\cdot 8(\\pi/4)} = 16 e^{2\\pi i} = 16$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 1: TALLER DE MATEMÁTICAS Y ESTADÍSTICA (TME)
    # ==========================================
    {
        "id": "tme_combinatoria_descriptiva",
        "title": "Combinatoria, Estadística Descriptiva y Covarianza Empírica",
        "course_id": "TME",
        "semester": 1,
        "domain": "prob_est",
        "xp": 10,
        "estimated_mins": 8,
        "prereqs": ["iag_induccion_sumatorias"],
        "encompasses": {"iag_induccion_sumatorias": 0.4},
        "generator_type": "descriptive_stats",
        "theory": (
            "**Conteo fundamental**:\n"
            "- Permutaciones de $n$: $n!$. Variaciones sin repetición de $k$ en $n$: $\\frac{n!}{(n-k)!}$.\n"
            "- Combinaciones (sin importar orden): $\\binom{n}{k} = \\frac{n!}{k!(n-k)!}$.\n\n"
            "**Estadísticos muestrales**:\n"
            "$$\\bar{x} = \\frac{1}{n}\\sum_{i=1}^n x_i, \\quad s_x^2 = \\frac{1}{n-1}\\sum_{i=1}^n (x_i - \\bar{x})^2, \\quad r_{xy} = \\frac{\\sum (x_i-\\bar{x})(y_i-\\bar{y})}{\\sqrt{\\sum (x_i-\\bar{x})^2 \\sum (y_i-\\bar{y})^2}} \\in [-1, 1]$$"
        ),
        "ds_connection": (
            "Notar que la correlación de Pearson $r_{xy}$ no es más que el **coseno del ángulo** entre los vectores centrados "
            "$\\tilde{x} = x - \\bar{x}\\mathbf{1}$ e $\\tilde{y} = y - \\bar{y}\\mathbf{1}$ en $\\mathbb{R}^n$."
        ),
        "uc_exam_tip": (
            "Si transformas linealmente una muestra mediante $y_i = a x_i + b$, recuerda que $\\bar{y} = a\\bar{x} + b$, "
            "mientras que la varianza ignora el desplazamiento: $s_y^2 = a^2 s_x^2$ y $s_y = |a| s_x$."
        ),
        "worked_example": {
            "problem": "Una muestra tiene media $\\bar{x} = 10$ y desviación estándar $s_x = 3$. Si definimos $y_i = -2x_i + 5$, halle $\\bar{y}$ y $s_y$.",
            "steps": [
                "Por linealidad del promedio: $\\bar{y} = -2\\bar{x} + 5 = -2(10) + 5 = -15$.",
                "Por propiedad de escala de la varianza: $s_y^2 = (-2)^2 s_x^2 = 4 \\cdot 9 = 36$.",
                "Por tanto, la desviación estándar es $s_y = |-2| s_x = 2 \\cdot 3 = 6$.",
            ],
            "final_answer": "$\\bar{y} = -15,\\; s_y = 6$",
        },
        "questions": [
            {
                "id": "q_tme_1",
                "type": "mcq",
                "prompt": "De un grupo de 6 ingenieros de datos y 4 estadísticos, ¿de cuántas formas se puede formar un comité de 3 personas que incluya al menos 1 estadístico?",
                "options": ["$100$", "$120$", "$80$", "$96$"],
                "correct_index": 0,
                "hint": "Usa el complemento: total de comités posibles $\\binom{10}{3}$ menos comités sin ningún estadístico $\\binom{6}{3}$.",
                "explanation": "El total sin restricciones es $\\binom{10}{3} = 120$. Los comités con 0 estadísticos son $\\binom{6}{3} = 20$. Por complemento: $120 - 20 = 100$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 2: CÁLCULO I (C1)
    # ==========================================
    {
        "id": "c1_derivadas_cadena",
        "title": "Regla de la Cadena, Derivación Implícita e Inversa",
        "course_id": "C1",
        "semester": 2,
        "domain": "calculo",
        "xp": 13,
        "estimated_mins": 10,
        "prereqs": ["ic_continuidad_derivada"],
        "encompasses": {"ic_continuidad_derivada": 0.8, "ic_funciones": 0.5},
        "generator_type": "derivative_chain",
        "theory": (
            "**Regla de la Cadena**: Si $g$ es derivable en $x$ y $f$ es derivable en $g(x)$, entonces:\n"
            "$$(f \\circ g)'(x) = f'(g(x)) \\cdot g'(x)$$\n"
            "**Derivada de la función inversa**: Si $f$ es biyectiva y $f'(a) \\neq 0$ con $b = f(a)$, entonces:\n"
            "$$(f^{-1})'(b) = \\frac{1}{f'(f^{-1}(b))} = \\frac{1}{f'(a)}$$"
        ),
        "ds_connection": (
            "El algoritmo de **Backpropagation** (retropropagación del error) que entrena todas las redes neuronales modernas "
            "es literalmente la aplicación sistemática de la Regla de la Cadena desde la función de pérdida hacia los pesos de cada capa."
        ),
        "uc_exam_tip": (
            "Cuando en una interrogación pidan $(f^{-1})'(b)$ para un polinomio como $f(x) = x^5 + 2x + 1$, **no intentes despejar $f^{-1}(y)$**. "
            "Resuelve a ojo qué valor pequeño de $a$ cumple $f(a) = b$ y aplica $1/f'(a)$."
        ),
        "worked_example": {
            "problem": "Sea $f(x) = x^3 + 2x + 1$. Calcule $(f^{-1})'(4)$.",
            "steps": [
                "Buscamos $a \\in \\mathbb{R}$ tal que $f(a) = 4$: probando $a = 1$, vemos que $f(1) = 1^3 + 2(1) + 1 = 4$, luego $f^{-1}(4) = 1$.",
                "Derivamos $f(x)$: $f'(x) = 3x^2 + 2$, por lo que $f'(1) = 3(1)^2 + 2 = 5$.",
                "Por el teorema de la función inversa: $(f^{-1})'(4) = \\frac{1}{f'(1)} = \\frac{1}{5}$.",
            ],
            "final_answer": "$\\frac{1}{5}$",
        },
        "questions": [
            {
                "id": "q_c1_cad_1",
                "type": "mcq",
                "prompt": "Si $h(x) = f(g(x))$ con $g(2) = 3$, $g'(2) = -4$, $f'(2) = 5$ y $f'(3) = 6$, ¿cuánto vale $h'(2)$?",
                "options": ["$-24$", "$-20$", "$30$", "$-12$"],
                "correct_index": 0,
                "hint": "Cuidado con dónde evalúas $f'$: recuerda que $h'(2) = f'(g(2)) \\cdot g'(2)$.",
                "explanation": "Por regla de la cadena, $h'(2) = f'(g(2)) \\cdot g'(2) = f'(3) \\cdot (-4) = 6 \\cdot (-4) = -24$.",
            }
        ],
    },
    {
        "id": "c1_tvm_optimizacion_taylor",
        "title": "Teorema del Valor Medio, Optimización y Polinomios de Taylor",
        "course_id": "C1",
        "semester": 2,
        "domain": "calculo",
        "xp": 14,
        "estimated_mins": 11,
        "prereqs": ["c1_derivadas_cadena"],
        "encompasses": {"c1_derivadas_cadena": 0.75, "ic_desigualdades": 0.4},
        "generator_type": "taylor_opt_1d",
        "theory": (
            "- **Teorema del Valor Medio (TVM)**: Si $f$ es continua en $[a,b]$ y derivable en $(a,b)$, existe $c \\in (a,b)$ tal que $f(b) - f(a) = f'(c)(b-a)$.\n"
            "- **Polinomio de Taylor de orden $n$ en $x=a$**:\n"
            "$$P_n(x) = \\sum_{k=0}^n \\frac{f^{(k)}(a)}{k!}(x-a)^k, \\quad R_n(x) = \\frac{f^{(n+1)}(\\xi)}{(n+1)!}(x-a)^{n+1}$$"
        ),
        "ds_connection": (
            "**XGBoost** y el método de **Newton-Raphson** aproximan la función de pérdida mediante su expansión de Taylor de segundo orden "
            "$L(w + \\Delta w) \\approx L(w) + g\\,\\Delta w + \\frac{1}{2} h\\,(\\Delta w)^2$ en cada iteración."
        ),
        "uc_exam_tip": (
            "Para demostrar desigualdades tipo $|\\sin x - \\sin y| \\le |x - y|$ o $\\ln(1+x) < x$ en interrogaciones de Cálculo I, "
            "aplica el TVM en $[x, y]$ y acota $|f'(c)|$."
        ),
        "worked_example": {
            "problem": "Encuentre el polinomio de Maclaurin (Taylor en $a=0$) de orden 2 de $f(x) = e^{2x} \\cos(x)$.",
            "steps": [
                "Usamos los desarrollos conocidos en $x=0$: $e^{2x} = 1 + 2x + 2x^2 + O(x^3)$ y $\\cos(x) = 1 - \\frac{x^2}{2} + O(x^4)$.",
                "Multiplicamos truncando términos de grado $> 2$:\n$$(1 + 2x + 2x^2)\\left(1 - \\frac{1}{2}x^2\\right) = 1 + 2x + \\left(2 - \\frac{1}{2}\\right)x^2 + O(x^3)$$",
            ],
            "final_answer": "$P_2(x) = 1 + 2x + \\frac{3}{2}x^2$",
        },
        "questions": [
            {
                "id": "q_c1_tay_1",
                "type": "mcq",
                "prompt": "Usando desarrollos de Taylor en $x=0$, ¿cuál es el valor de $\\lim_{x \\to 0} \\frac{e^x - 1 - x}{x^2}$?",
                "options": ["$1/2$", "$1$", "$0$", "$2$"],
                "correct_index": 0,
                "hint": "Sustituye $e^x = 1 + x + \\frac{x^2}{2!} + O(x^3)$.",
                "explanation": "El numerador es $(1 + x + x^2/2 + O(x^3)) - 1 - x = \\frac{1}{2}x^2 + O(x^3)$. Dividiendo por $x^2$ y tomando $x \\to 0$ se obtiene $1/2$.",
            }
        ],
    },
    {
        "id": "c1_integracion_tfc",
        "title": "Integral de Riemann, Teorema Fundamental del Cálculo y Técnicas",
        "course_id": "C1",
        "semester": 2,
        "domain": "calculo",
        "xp": 14,
        "estimated_mins": 12,
        "prereqs": ["c1_tvm_optimizacion_taylor"],
        "encompasses": {"c1_tvm_optimizacion_taylor": 0.7, "c1_derivadas_cadena": 0.6, "iag_induccion_sumatorias": 0.4},
        "generator_type": "definite_integral",
        "theory": (
            "**Teorema Fundamental del Cálculo (TFC Parte 1 con Regla de Leibniz)**:\n"
            "$$\\frac{d}{dx} \\left( \\int_{g(x)}^{h(x)} f(t)\\,dt \\right) = f(h(x))\\cdot h'(x) - f(g(x))\\cdot g'(x)$$\n"
            "**Integración por Partes**: $\\int u\\,dv = u\\,v - \\int v\\,du$.\n"
            "**Integrales Impropias de referencia**: $\\int_1^\\infty \\frac{dx}{x^p}$ converge $\\iff p > 1$; mientras que $\\int_0^1 \\frac{dx}{x^p}$ converge $\\iff p < 1$."
        ),
        "ds_connection": (
            "En Probabilidad y Estadística Bayesiana, calcular esperanzas $\\mathbb{E}[g(X)] = \\int_{-\\infty}^{\\infty} g(x)f(x)\\,dx$, "
            "funciones de distribución acumulada $F(x) = \\int_{-\\infty}^x f(t)\\,dt$ y constantes de normalización requiere dominar el TFC e integrales impropias."
        ),
        "uc_exam_tip": (
            "La pregunta de derivar $G(x) = \\int_{\\alpha(x)}^{\\beta(x)} f(t)\\,dt$ aparece en **casi todas** las I3 y Exámenes de Cálculo I en la UC. "
            "Nunca olvides multiplicar por las derivadas de los límites de integración $\\beta'(x)$ y $\\alpha'(x)$."
        ),
        "worked_example": {
            "problem": "Sea $F(x) = \\int_{0}^{x^2} e^{-t^2}\\,dt$. Calcule $F'(x)$.",
            "steps": [
                "Identificamos el integrando $f(t) = e^{-t^2}$ y el límite superior $h(x) = x^2$.",
                "Por el TFC + Regla de la Cadena: $F'(x) = f(h(x)) \\cdot h'(x)$.",
                "Evaluamos $f(x^2) = e^{-(x^2)^2} = e^{-x^4}$ y multiplicamos por $h'(x) = 2x$.",
            ],
            "final_answer": "$F'(x) = 2x e^{-x^4}$",
        },
        "questions": [
            {
                "id": "q_c1_int_1",
                "type": "mcq",
                "prompt": "¿Para qué valores de $p \\in \\mathbb{R}$ converge la integral impropia $\\int_2^{\\infty} \\frac{1}{x^p}\\,dx$?",
                "options": ["$p > 1$", "$p \\ge 1$", "$p < 1$", "$p > 0$"],
                "correct_index": 0,
                "hint": "Para $p=1$ la primitiva es $\\ln(x)$, que diverge cuando $x \\to \\infty$.",
                "explanation": "La primitiva de $x^{-p}$ para $p \\neq 1$ es $\\frac{x^{1-p}}{1-p}$, que tiene límite finito en $+\\infty$ si y solo si $1 - p < 0 \\iff p > 1$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 2: ÁLGEBRA LINEAL PARA CIENCIA DE DATOS (ALCD)
    # ==========================================
    {
        "id": "al_sistemas_rango",
        "title": "Eliminación Gaussiana, Matrices y Rango",
        "course_id": "ALCD",
        "semester": 2,
        "domain": "algebra",
        "xp": 12,
        "estimated_mins": 10,
        "prereqs": ["iag_vectores_geometria"],
        "encompasses": {"iag_vectores_geometria": 0.7},
        "generator_type": "matrix_rank_system",
        "theory": (
            "Un sistema lineal $Ax = b$ ($A \\in \\mathbb{R}^{m \\times n}$) es **compatible** si y solo si $\\text{rango}(A) = \\text{rango}([A \\mid b])$.\n"
            "- Si $\\text{rango}(A) = \\text{rango}([A\\mid b]) = n$ (número de incógnitas): **solución única**.\n"
            "- Si $\\text{rango}(A) = \\text{rango}([A\\mid b]) = r < n$: **infinitas soluciones** con $n - r$ variables libres.\n"
            "- Si $\\text{rango}(A) < \\text{rango}([A\\mid b])$: **incompatible** (sin solución)."
        ),
        "ds_connection": (
            "En un dataset $X \\in \\mathbb{R}^{n \\times p}$, el rango $\\text{rango}(X)$ indica cuántas variables (features) son realmente independientes; "
            "si $\\text{rango}(X) < p$, existe **multicolinealidad exacta** y $(X^T X)$ no es invertible."
        ),
        "uc_exam_tip": (
            "En sistemas con parámetro $k \\in \\mathbb{R}$, escalona evitando dividir por expresiones con $k$ hasta el final; "
            "luego analiza por separado cada valor de $k$ que anula un pivote."
        ),
        "worked_example": {
            "problem": "Determine para qué valor de $k$ el sistema $\\begin{cases} x + 2y = 3 \\\\ 2x + ky = 6 \\end{cases}$ tiene infinitas soluciones.",
            "steps": [
                "Formamos la matriz ampliada $\\begin{pmatrix} 1 & 2 & 3 \\\\ 2 & k & 6 \\end{pmatrix}$ y operamos $F_2 \\leftarrow F_2 - 2F_1$.",
                "Obtenemos $\\begin{pmatrix} 1 & 2 & 3 \\\\ 0 & k-4 & 0 \\end{pmatrix}$.",
                "Para tener infinitas soluciones necesitamos $\\text{rango}(A) = \\text{rango}([A\\mid b]) = 1 < 2$, lo cual ocurre cuando $k - 4 = 0 \\implies k = 4$.",
            ],
            "final_answer": "$k = 4$",
        },
        "questions": [
            {
                "id": "q_al_sis_1",
                "type": "mcq",
                "prompt": "Si $A$ es una matriz de $4 \\times 6$ con $\\text{rango}(A) = 4$, ¿cuántas variables libres tiene el sistema homogéneo $Ax = 0$?",
                "options": ["$2$", "$4$", "$0$", "$6$"],
                "correct_index": 0,
                "hint": "El número de variables libres (dimensión del núcleo) es $n - \\text{rango}(A)$, donde $n$ es el número de columnas.",
                "explanation": "Por el Teorema del Rango-Nulidad, $\\dim(\\ker A) = n - \\text{rango}(A) = 6 - 4 = 2$ variables libres.",
            }
        ],
    },
    {
        "id": "al_espacios_nucleo_imagen",
        "title": "Subespacios, Base, Dimensión y Teorema Rango-Nulidad",
        "course_id": "ALCD",
        "semester": 2,
        "domain": "algebra",
        "xp": 13,
        "estimated_mins": 10,
        "prereqs": ["al_sistemas_rango"],
        "encompasses": {"al_sistemas_rango": 0.8},
        "generator_type": "rank_nullity",
        "theory": (
            "Para toda matriz $A \\in \\mathbb{R}^{m \\times n}$ (o transformación lineal $T: \\mathbb{R}^n \\to \\mathbb{R}^m$):\n"
            "- **Núcleo (Nullspace)**: $\\ker(A) = \\{x \\in \\mathbb{R}^n : Ax = 0\\} \\subseteq \\mathbb{R}^n$.\n"
            "- **Imagen (Column space)**: $\\text{Im}(A) = \\text{Col}(A) = \\{Ax : x \\in \\mathbb{R}^n\\} \\subseteq \\mathbb{R}^m$.\n"
            "- **Teorema del Rango-Nulidad**:\n"
            "$$\\dim(\\ker A) + \\dim(\\text{Im } A) = n \\quad (\\text{número de columnas de } A)$$"
        ),
        "ds_connection": (
            "El espacio columna $\\text{Col}(X)$ de tu matriz de datos contiene todas las predicciones posibles $\\hat{y} = X\\beta$ de un modelo lineal."
        ),
        "uc_exam_tip": (
            "Para probar que $W \\subseteq V$ **no** es subespacio vectorial, basta exhibir que $0 \\notin W$ o dar un contraejemplo numérico "
            "donde falle la suma o la ponderación escalar."
        ),
        "worked_example": {
            "problem": "Sea $W = \\{(x, y, z) \\in \\mathbb{R}^3 : x - 2y + 3z = 0\\}$. Encuentre una base de $W$ y su dimensión.",
            "steps": [
                "Despejamos la variable pivote $x = 2y - 3z$ con $y, z \\in \\mathbb{R}$ libres.",
                "Escribimos el vector genérico: $(2y - 3z, y, z) = y(2, 1, 0) + z(-3, 0, 1)$.",
                "Los vectores $\\{(2,1,0), (-3,0,1)\\}$ generan $W$ y son linealmente independientes, por lo que forman una base y $\\dim(W) = 2$.",
            ],
            "final_answer": "Base $\\{(2,1,0), (-3,0,1)\\}$, $\\dim(W) = 2$",
        },
        "questions": [
            {
                "id": "q_al_esp_1",
                "type": "mcq",
                "prompt": "Sea $T: \\mathbb{R}^5 \\to \\mathbb{R}^3$ una transformación lineal sobreyectiva. ¿Cuál es la dimensión de $\\ker(T)$?",
                "options": ["$2$", "$3$", "$0$", "$5$"],
                "correct_index": 0,
                "hint": "Si $T$ es sobreyectiva hacia $\\mathbb{R}^3$, entonces $\\dim(\\text{Im } T) = 3$.",
                "explanation": "Por el Teorema de las Dimensiones, $\\dim(\\ker T) = \\dim(\\mathbb{R}^5) - \\dim(\\text{Im } T) = 5 - 3 = 2$.",
            }
        ],
    },
    {
        "id": "al_ortogonalidad_minimos_cuadrados",
        "title": "Ortogonalidad, Proyecciones y Mínimos Cuadrados (OLS)",
        "course_id": "ALCD",
        "semester": 2,
        "domain": "algebra",
        "xp": 15,
        "estimated_mins": 12,
        "prereqs": ["al_espacios_nucleo_imagen"],
        "encompasses": {"al_espacios_nucleo_imagen": 0.8, "iag_vectores_geometria": 0.7},
        "generator_type": "least_squares_1d",
        "theory": (
            "Cuando el sistema $Ax = b$ es sobredeterminado e incompatible ($b \\notin \\text{Col}(A)$), buscamos $\\hat{x}$ que minimice el error cuadrático $\\|Ax - b\\|_2^2$.\n"
            "Geométricamente, $A\\hat{x}$ es la **proyección ortogonal** de $b$ sobre $\\text{Col}(A)$, por lo que el residuo $r = b - A\\hat{x}$ es ortogonal a $\\text{Col}(A)$ ($A^T(b - A\\hat{x}) = 0$), dando las **Ecuaciones Normales**:\n"
            "$$A^T A \\hat{x} = A^T b \\implies \\hat{x} = (A^T A)^{-1} A^T b$$\n"
            "(cuando las columnas de $A$ son linealmente independientes)."
        ),
        "ds_connection": (
            "¡Esta es la ecuación más importante de Regresión Lineal (`LinearRegression` en scikit-learn)! "
            "La matriz de proyección $P = A(A^TA)^{-1}A^T$ es la famosa **Hat Matrix** ($H$) en estadística porque le pone el sombrero a $y$: $\\hat{y} = Hy$."
        ),
        "uc_exam_tip": (
            "Recuerda siempre las dos propiedades clave de una matriz de proyección ortogonal $P$: es **simétrica** ($P^T = P$) e **idempotente** ($P^2 = P$). "
            "Para verificar tu solución $\\hat{x}$ en un examen, comprueba que el vector error $e = b - A\\hat{x}$ tenga producto punto $0$ con cada columna de $A$."
        ),
        "worked_example": {
            "problem": "Ajuste por mínimos cuadrados el modelo $y = \\beta x$ (sin intercepto) a los puntos $(1, 2)$, $(2, 3)$ y $(3, 7)$.",
            "steps": [
                "Planteamos $A = \\begin{pmatrix} 1 \\\\ 2 \\\\ 3 \\end{pmatrix}$ y $b = \\begin{pmatrix} 2 \\\\ 3 \\\\ 7 \\end{pmatrix}$.",
                "Calculamos $A^T A = 1^2 + 2^2 + 3^2 = 14$ y $A^T b = 1(2) + 2(3) + 3(7) = 29$.",
                "Por la ecuación normal $A^T A \\hat{\\beta} = A^T b$: $14\\hat{\\beta} = 29 \\implies \\hat{\\beta} = \\frac{29}{14}$.",
            ],
            "final_answer": "$\\hat{\\beta} = \\frac{29}{14}$",
        },
        "questions": [
            {
                "id": "q_al_ols_1",
                "type": "mcq",
                "prompt": "Si $\\hat{x}$ es la solución de mínimos cuadrados de $Ax \\approx b$, ¿cuál de las siguientes igualdades es SIEMPRE verdadera?",
                "options": [
                    "$A^T(b - A\\hat{x}) = 0$",
                    "$b - A\\hat{x} = 0$",
                    "$A(b - A\\hat{x}) = 0$",
                    "$\\hat{x}^T b = 0$",
                ],
                "correct_index": 0,
                "hint": "El vector residuo $r = b - A\\hat{x}$ es ortogonal al espacio columna $\\text{Col}(A)$, que es equivalente a estar en $\\ker(A^T)$.",
                "explanation": "Por ortogonalidad del residuo respecto a cada columna de $A$, se cumple $A^T(b - A\\hat{x}) = 0$, que es exactamente la ecuación normal $A^TA\\hat{x} = A^Tb$.",
            }
        ],
    },
    {
        "id": "al_valores_propios",
        "title": "Valores y Vectores Propios, Traza, Determinante y Diagonalización",
        "course_id": "ALCD",
        "semester": 2,
        "domain": "algebra",
        "xp": 15,
        "estimated_mins": 12,
        "prereqs": ["al_espacios_nucleo_imagen", "iag_complejos_polinomios"],
        "encompasses": {"al_espacios_nucleo_imagen": 0.75, "iag_complejos_polinomios": 0.5},
        "generator_type": "eigenvalues_2x2",
        "theory": (
            "Un escalar $\\lambda$ es **valor propio (eigenvalue)** de $A \\in \\mathbb{R}^{n \\times n}$ si existe $v \\neq 0$ tal que $Av = \\lambda v$, "
            "lo que equivale a $\\det(A - \\lambda I) = 0$.\n\n"
            "**Invariantes espectrales rápidos**:\n"
            "$$\\text{tr}(A) = \\sum_{i=1}^n a_{ii} = \\sum_{i=1}^n \\lambda_i, \\qquad \\det(A) = \\prod_{i=1}^n \\lambda_i$$\n"
            "Si $A = P D P^{-1}$, entonces $A^k = P D^k P^{-1}$."
        ),
        "ds_connection": (
            "En **PCA (Análisis de Componentes Principales)**, las direcciones de máxima varianza son los vectores propios de la matriz de covarianza $\\Sigma$, "
            "y cada valor propio $\\lambda_i$ mide exactamente la varianza explicada por esa componente."
        ),
        "uc_exam_tip": (
            "En matrices de $2 \\times 2$, el polinomio característico siempre es $\\lambda^2 - \\text{tr}(A)\\lambda + \\det(A) = 0$. "
            "Usa la traza y el determinante para encontrar los valores propios mentalmente en segundos."
        ),
        "worked_example": {
            "problem": "Halle los valores propios de $A = \\begin{pmatrix} 4 & 2 \\\\ 1 & 3 \\end{pmatrix}$.",
            "steps": [
                "Calculamos la traza $\\text{tr}(A) = 4 + 3 = 7$ y el determinante $\\det(A) = 4(3) - 2(1) = 10$.",
                "El polinomio característico es $\\lambda^2 - 7\\lambda + 10 = (\\lambda - 5)(\\lambda - 2) = 0$.",
                "Por lo tanto, los valores propios son $\\lambda_1 = 5$ y $\\lambda_2 = 2$.",
            ],
            "final_answer": "$\\lambda_1 = 5,\\; \\lambda_2 = 2$",
        },
        "questions": [
            {
                "id": "q_al_eig_1",
                "type": "mcq",
                "prompt": "Si $A \\in \\mathbb{R}^{3 \\times 3}$ tiene valores propios $\\lambda_1 = 2, \\lambda_2 = -1, \\lambda_3 = 4$, ¿cuánto vale la traza de $A^2$?",
                "options": ["$21$", "$25$", "$5$", "$16$"],
                "correct_index": 0,
                "hint": "Los valores propios de $A^2$ son $\\lambda_1^2, \\lambda_2^2, \\lambda_3^2$, y la traza es la suma de los valores propios.",
                "explanation": "Los valores propios de $A^2$ son $2^2 = 4$, $(-1)^2 = 1$ y $4^2 = 16$. Por tanto, $\\text{tr}(A^2) = 4 + 1 + 16 = 21$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 3 (ANTICIPACIÓN): CÁLCULO PARA CIENCIA DE DATOS (CCD)
    # ==========================================
    {
        "id": "ccd_gradiente_hessiana",
        "title": "Derivadas Parciales, Vector Gradiente y Matriz Hessiana",
        "course_id": "CCD",
        "semester": 3,
        "domain": "calculo",
        "xp": 15,
        "estimated_mins": 12,
        "prereqs": ["c1_tvm_optimizacion_taylor", "al_valores_propios"],
        "encompasses": {"c1_tvm_optimizacion_taylor": 0.75, "al_valores_propios": 0.5, "iag_vectores_geometria": 0.5},
        "generator_type": "gradient_eval",
        "theory": (
            "Para $f: \\mathbb{R}^n \\to \\mathbb{R}$ diferenciable:\n"
            "- El **vector gradiente** $\\nabla f(x) = \\left(\\frac{\\partial f}{\\partial x_1}, \\dots, \\frac{\\partial f}{\\partial x_n}\\right)^T$ apunta en la dirección de **máximo crecimiento** de $f$, con tasa máxima $\\|\\nabla f(x)\\|_2$.\n"
            "- La **derivada direccional** en dirección unitaria $u$ es $D_u f(x) = \\nabla f(x) \\cdot u$.\n"
            "- La **Matriz Hessiana** $\\nabla^2 f(x) = \\left[\\frac{\\partial^2 f}{\\partial x_i \\partial x_j}\\right]$ (simétrica por Teorema de Schwarz) clasifica puntos críticos donde $\\nabla f(x^*) = 0$."
        ),
        "ds_connection": (
            "Para minimizar una función de pérdida $L(\\theta)$, nos movemos en la dirección opuesta al gradiente: "
            "$\\theta_{t+1} = \\theta_t - \\eta \\nabla L(\\theta_t)$. Además, para la forma cuadrática $f(x) = \\frac{1}{2}x^T A x - b^T x$ (con $A$ simétrica), "
            "$\\nabla f(x) = Ax - b$ y $\\nabla^2 f(x) = A$."
        ),
        "uc_exam_tip": (
            "Aprende de memoria las derivadas matriciales: $\\nabla_x (b^T x) = b$ y $\\nabla_x (x^T A x) = (A + A^T)x$ (que se reduce a $2Ax$ cuando $A$ es simétrica). "
            "Te ahorrarán páginas enteras de álgebra en Cálculo para Ciencia de Datos y Optimización."
        ),
        "worked_example": {
            "problem": "Sea $f(x, y) = x^2 y + 3y^2$. Calcule $\\nabla f(1, 2)$ y la tasa máxima de crecimiento desde $(1, 2)$.",
            "steps": [
                "Calculamos las derivadas parciales: $\\frac{\\partial f}{\\partial x} = 2xy$ y $\\frac{\\partial f}{\\partial y} = x^2 + 6y$.",
                "Evaluamos en $(1, 2)$: $\\nabla f(1, 2) = (2(1)(2),\\; 1^2 + 6(2))^T = (4, 13)^T$.",
                "La tasa máxima de crecimiento es la norma del gradiente: $\\|\\nabla f(1, 2)\\| = \\sqrt{4^2 + 13^2} = \\sqrt{185}$.",
            ],
            "final_answer": "$\\nabla f(1,2) = (4, 13)^T,\\quad \\|\\nabla f(1,2)\\| = \\sqrt{185}$",
        },
        "questions": [
            {
                "id": "q_ccd_grad_1",
                "type": "mcq",
                "prompt": "Si $A \\in \\mathbb{R}^{n \\times n}$ es una matriz simétrica y $f(x) = \\frac{1}{2} x^T A x - b^T x$, ¿cuáles son el gradiente $\\nabla f(x)$ y la Hessiana $\\nabla^2 f(x)$?",
                "options": [
                    "$\\nabla f(x) = Ax - b, \\quad \\nabla^2 f(x) = A$",
                    "$\\nabla f(x) = 2Ax - b, \\quad \\nabla^2 f(x) = 2A$",
                    "$\\nabla f(x) = x^T A - b^T, \\quad \\nabla^2 f(x) = I$",
                    "$\\nabla f(x) = Ax, \\quad \\nabla^2 f(x) = A^T A$",
                ],
                "correct_index": 0,
                "hint": "Usa que para $A$ simétrica, $\\nabla(x^T A x) = 2Ax$.",
                "explanation": "Como $A = A^T$, $\\nabla\\left(\\frac{1}{2}x^T A x\\right) = \\frac{1}{2}(2Ax) = Ax$, y $\\nabla(b^T x) = b$. Derivando nuevamente respecto a $x$ obtenemos $\\nabla^2 f(x) = A$.",
            }
        ],
    },
    {
        "id": "ccd_lagrange_multivariable",
        "title": "Multiplicadores de Lagrange e Integrales Múltiples",
        "course_id": "CCD",
        "semester": 3,
        "domain": "calculo",
        "xp": 15,
        "estimated_mins": 12,
        "prereqs": ["ccd_gradiente_hessiana", "c1_integracion_tfc"],
        "encompasses": {"ccd_gradiente_hessiana": 0.8, "c1_integracion_tfc": 0.6},
        "generator_type": "lagrange_linear_sphere",
        "theory": (
            "**Multiplicadores de Lagrange**: Para optimizar $f(x)$ sujeto a la restricción $g(x) = c$, los extremos cumplen que los gradientes son colineales:\n"
            "$$\\nabla f(x^*) = \\lambda \\nabla g(x^*), \\qquad g(x^*) = c$$\n"
            "**Cambio de Variable en Integrales Múltiples**: $\\iint_R f(x,y)\\,dx\\,dy = \\iint_{R^*} f(x(u,v), y(u,v))\\,|\\det J(u,v)|\\,du\\,dv$. "
            "En polares ($x=r\\cos\\theta, y=r\\sin\\theta$), el Jacobiano es $|\\det J| = r$."
        ),
        "ds_connection": (
            "Maximizar la varianza proyectada $u^T \\Sigma u$ sujeto a $\\|u\\|^2 = 1$ mediante Lagrange da $\\nabla(u^T\\Sigma u) = \\lambda \\nabla(u^T u) \\implies 2\\Sigma u = 2\\lambda u \\implies \\Sigma u = \\lambda u$: "
            "¡la demostración exacta de por qué PCA usa vectores propios! Y el cambio a polares permite demostrar que $\\int_{-\\infty}^{\\infty} e^{-x^2/2}dx = \\sqrt{2\\pi}$ (normalización de la Gaussiana)."
        ),
        "uc_exam_tip": (
            "Para maximizar una función lineal $f(x) = c^T x$ sobre la esfera $\\|x\\|_2^2 = R^2$, por Lagrange (o Cauchy-Schwarz) el máximo siempre es $\\|c\\|_2 \\cdot R$."
        ),
        "worked_example": {
            "problem": "Encuentre el valor máximo de $f(x, y) = 3x + 4y$ sujeto a $x^2 + y^2 = 1$.",
            "steps": [
                "Planteamos $\\nabla f = \\lambda \\nabla g \\implies (3, 4) = \\lambda (2x, 2y)$, de donde $x = \\frac{3}{2\\lambda}$ e $y = \\frac{4}{2\\lambda}$.",
                "Sustituimos en la restricción $x^2 + y^2 = 1$: $\\frac{9 + 16}{4\\lambda^2} = 1 \\implies 4\\lambda^2 = 25 \\implies 2\\lambda = \\pm 5$.",
                "Con $2\\lambda = 5$, obtenemos $(x^*, y^*) = (3/5, 4/5)$ y el valor máximo $f(3/5, 4/5) = \\frac{9+16}{5} = 5$.",
            ],
            "final_answer": "$5$",
        },
        "questions": [
            {
                "id": "q_ccd_lag_1",
                "type": "mcq",
                "prompt": "Al calcular la integral gaussiana $I = \\iint_{\\mathbb{R}^2} e^{-(x^2+y^2)}\\,dx\\,dy$ usando coordenadas polares, ¿qué valor se obtiene?",
                "options": ["$\\pi$", "$\\sqrt{\\pi}$", "$2\\pi$", "$1$"],
                "correct_index": 0,
                "hint": "En polares $dx\\,dy = r\\,dr\\,d\\theta$ con $\\theta \\in [0, 2\\pi]$ y $r \\in [0, \\infty)$.",
                "explanation": "$I = \\int_0^{2\\pi} d\\theta \\int_0^\\infty r e^{-r^2} dr = 2\\pi \\left[-\\frac{1}{2}e^{-r^2}\\right]_0^\\infty = 2\\pi \\cdot \\frac{1}{2} = \\pi$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 3 (ANTICIPACIÓN): ÁLGEBRA LINEAL AVANZADA Y MODELAMIENTO (ALAM)
    # ==========================================
    {
        "id": "alam_svd_pca",
        "title": "Matrices Definidas Positivas, SVD y Aproximación de Bajo Rango (PCA)",
        "course_id": "ALAM",
        "semester": 3,
        "domain": "algebra",
        "xp": 16,
        "estimated_mins": 13,
        "prereqs": ["al_valores_propios", "al_ortogonalidad_minimos_cuadrados"],
        "encompasses": {"al_valores_propios": 0.85, "al_ortogonalidad_minimos_cuadrados": 0.75},
        "generator_type": "svd_singular_values",
        "theory": (
            "- Una matriz simétrica $S \\in \\mathbb{R}^{n \\times n}$ es ** Semidefinida Positiva** ($S \\succeq 0$) si $x^T S x \\ge 0$ para todo $x$, lo cual equivale a que todos sus valores propios cumplan $\\lambda_i \\ge 0$. Toda matriz de la forma $A^T A$ es siempre $S \\succeq 0$.\n"
            "- **Descomposición en Valores Singulares (SVD)**: Toda matriz $A \\in \\mathbb{R}^{m \\times n}$ se factoriza como:\n"
            "$$A = U \\Sigma V^T = \\sum_{i=1}^r \\sigma_i u_i v_i^T$$\n"
            "donde $\\sigma_1 \\ge \\sigma_2 \\ge \\dots \\ge \\sigma_r > 0$ con $\\sigma_i = \\sqrt{\\lambda_i(A^T A)}$.\n"
            "- **Teorema de Eckart-Young**: La mejor aproximación de rango $k < r$ de $A$ (en norma de Frobenius o espectral) se obtiene truncando la SVD a los $k$ mayores valores singulares: $A_k = \\sum_{i=1}^k \\sigma_i u_i v_i^T$."
        ),
        "ds_connection": (
            "La SVD es la joya de la corona de Ciencia de Datos: compresión de imágenes, reducción de dimensionalidad (PCA), "
            "sistemas recomendadores matriciales, LSA en texto y adaptación eficiente de LLMs (**LoRA: Low-Rank Adaptation**) son todos aplicaciones directas de Eckart-Young."
        ),
        "uc_exam_tip": (
            "Recuerda la relación con las normas matriciales: la **norma espectral** $\\|A\\|_2 = \\sigma_1$ (el mayor valor singular) "
            "y la **norma de Frobenius** $\\|A\\|_F = \\sqrt{\\sum_{i,j} a_{ij}^2} = \\sqrt{\\text{tr}(A^T A)} = \\sqrt{\\sum_{i=1}^r \\sigma_i^2}$."
        ),
        "worked_example": {
            "problem": "Si $A \\in \\mathbb{R}^{100 \\times 50}$ tiene valores singulares $\\sigma_1 = 10, \\sigma_2 = 6, \\sigma_3 = 2$ y el resto cero, ¿cuál es el error en norma de Frobenius $\\|A - A_1\\|_F$ de su mejor aproximación de rango 1?",
            "steps": [
                "Por el Teorema de Eckart-Young, la mejor aproximación de rango 1 es $A_1 = \\sigma_1 u_1 v_1^T$.",
                "El residuo es $A - A_1 = \\sigma_2 u_2 v_2^T + \\sigma_3 u_3 v_3^T$.",
                "Su norma de Frobenius es $\\|A - A_1\\|_F = \\sqrt{\\sigma_2^2 + \\sigma_3^2} = \\sqrt{6^2 + 2^2} = \\sqrt{40} = 2\\sqrt{10}$.",
            ],
            "final_answer": "$\\sqrt{40} = 2\\sqrt{10}$",
        },
        "questions": [
            {
                "id": "q_alam_svd_1",
                "type": "mcq",
                "prompt": "Si los valores propios de $A^T A$ son $25, 9$ y $0$, ¿cuánto vale la norma espectral $\\|A\\|_2$ (mayor valor singular de $A$)?",
                "options": ["$5$", "$25$", "$\\sqrt{34}$", "$3$"],
                "correct_index": 0,
                "hint": "Los valores singulares de $A$ son las raíces cuadradas de los valores propios de $A^T A$.",
                "explanation": "Los valores singulares son $\\sigma_1 = \\sqrt{25} = 5$ y $\\sigma_2 = \\sqrt{9} = 3$. La norma espectral es $\\|A\\|_2 = \\sigma_1 = 5$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 3 (ANTICIPACIÓN): MATEMÁTICAS DISCRETAS (MD)
    # ==========================================
    {
        "id": "md_asintotica_grafos",
        "title": "Complejidad Asintótica (Big-O), Recurrencias y Teoría de Grafos",
        "course_id": "MD",
        "semester": 3,
        "domain": "discretas_opt",
        "xp": 13,
        "estimated_mins": 10,
        "prereqs": ["iag_induccion_sumatorias", "ic_limites"],
        "encompasses": {"iag_induccion_sumatorias": 0.65, "ic_limites": 0.45},
        "generator_type": "graph_handshaking",
        "theory": (
            "- **Orden Asintótico**: $f(n) = O(g(n))$ si existen $C > 0, n_0$ tales que $0 \\le f(n) \\le C g(n)$ para todo $n \\ge n_0$.\n"
            "  Jerarquía: $1 \\ll \\log n \\ll \\sqrt{n} \\ll n \\ll n\\log n \\ll n^2 \\ll 2^n \\ll n!$.\n"
            "- **Teorema Maestro** para $T(n) = a T(n/b) + \\Theta(n^d)$: si $d = \\log_b a$, entonces $T(n) = \\Theta(n^d \\log n)$.\n"
            "- **Grafos**: En todo grafo no dirigido $G = (V, E)$, el **Lema del Apretón de Manos** establece:\n"
            "$$\\sum_{v \\in V} \\deg(v) = 2|E|$$\n"
            "Un **árbol** de $n$ vértices es conexo, acíclico y siempre tiene exactamente $|E| = n - 1$ aristas."
        ),
        "ds_connection": (
            "Saber distinguir entre un algoritmo $O(n^2)$ y uno $O(n \\log n)$ determina si tu pipeline de datos procesa 10 millones de filas en 2 segundos o en 3 días. "
            "Además, los Árboles de Decisión y Graph Neural Networks (GNNs) se apoyan directamente en teoría de grafos."
        ),
        "uc_exam_tip": (
            "En IIC1253 (Matemáticas Discretas), el Lema del Apretón de Manos $\\sum \\deg(v) = 2|E|$ y la caracterización de árboles ($|E| = |V| - 1$) "
            "resuelven de inmediato problemas sobre grados de vértices y componentes conexas."
        ),
        "worked_example": {
            "problem": "Un árbol $T$ tiene 4 vértices de grado 3, 2 vértices de grado 2 y el resto son hojas (grado 1). ¿Cuántas hojas tiene $T$?",
            "steps": [
                "Sea $h$ el número de hojas. Entonces el número total de vértices es $|V| = 4 + 2 + h = 6 + h$.",
                "Por ser un árbol, el número de aristas es $|E| = |V| - 1 = 5 + h$.",
                "Por el lema de los grados $\\sum \\deg(v) = 2|E|$: $4(3) + 2(2) + h(1) = 2(5 + h) \\implies 16 + h = 10 + 2h \\implies h = 6$.",
            ],
            "final_answer": "$6$ hojas",
        },
        "questions": [
            {
                "id": "q_md_1",
                "type": "mcq",
                "prompt": "¿Cuál es la complejidad asintótica de la recurrencia de MergeSort $T(n) = 2T(n/2) + \\Theta(n)$?",
                "options": [
                    "$\\Theta(n \\log n)$",
                    "$\\Theta(n^2)$",
                    "$\\Theta(n)$",
                    "$\\Theta(\\log n)$",
                ],
                "correct_index": 0,
                "hint": "En el Teorema Maestro tienes $a = 2, b = 2, d = 1$, luego $\\log_b a = \\log_2 2 = 1 = d$.",
                "explanation": "Al tener $\\log_2(2) = 1 = d$, estamos en el caso equilibrado del Teorema Maestro, por lo que $T(n) = \\Theta(n \\log n)$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 4 (ANTICIPACIÓN): OPTIMIZACIÓN PARA CIENCIA DE DATOS (OCD)
    # ==========================================
    {
        "id": "ocd_convexidad_descenso_gradiente",
        "title": "Funciones Convexas y Convergencia de Descenso de Gradiente",
        "course_id": "OCD",
        "semester": 4,
        "domain": "discretas_opt",
        "xp": 16,
        "estimated_mins": 13,
        "prereqs": ["ccd_lagrange_multivariable", "alam_svd_pca"],
        "encompasses": {"ccd_lagrange_multivariable": 0.8, "alam_svd_pca": 0.7, "ccd_gradiente_hessiana": 0.85},
        "generator_type": "gradient_descent_step",
        "theory": (
            "Una función dos veces diferenciable $f: \\mathbb{R}^n \\to \\mathbb{R}$ es **convexa** si y solo si su matriz Hessiana es semidefinida positiva en todo punto: $\\nabla^2 f(x) \\succeq 0$.\n"
            "- **Propiedad Fundamental de la Convexidad**: En una función convexa, **todo mínimo local es un mínimo global**, y si es diferenciable sin restricciones, $x^*$ es óptimo global $\\iff \\nabla f(x^*) = 0$.\n"
            "- **Descenso de Gradiente**: $x_{k+1} = x_k - \\eta \\nabla f(x_k)$. Si $\\nabla f$ es $L$-Lipschitz ($\\|\\nabla^2 f(x)\\|_2 \\le L$), el paso garantiza descenso monótono para tasas de aprendizaje $0 < \\eta < \\frac{2}{L}$ (siendo el paso óptimo $\\eta = \\frac{1}{L}$ en cotas estándar)."
        ),
        "ds_connection": (
            "Entender por qué la regresión logística, SVM y Ridge ($\\frac{1}{2}\\|Ax-b\\|_2^2 + \\frac{\\lambda}{2}\\|x\\|_2^2$) son **estrictamente convexos** "
            "y cómo el mayor valor propio $L = \\lambda_{\\max}(A^TA)$ limita la tasa de aprendizaje $\\eta$ explica por qué estandarizar tus variables acelera dramáticamente el entrenamiento."
        ),
        "uc_exam_tip": (
            "Para demostrar en un control o interrogación que $f(x)$ es convexa, calcula $\\nabla^2 f(x)$ y verifica que sus valores propios sean $\\ge 0$ "
            "(en $\\mathbb{R}^2$, basta $\\text{tr}(\\nabla^2 f) \\ge 0$ y $\\det(\\nabla^2 f) \\ge 0$)."
        ),
        "worked_example": {
            "problem": "Sea $f(x, y) = x^2 + 2y^2$. Partiendo de $x_0 = (2, 1)^T$ con tasa de aprendizaje $\\eta = \\frac{1}{4}$, calcule la primera iteración $x_1$ de descenso de gradiente.",
            "steps": [
                "Calculamos el gradiente: $\\nabla f(x, y) = (2x, 4y)^T$.",
                "Evaluamos en $x_0 = (2, 1)^T$: $\\nabla f(2, 1) = (4, 4)^T$.",
                "Actualizamos $x_1 = x_0 - \\eta \\nabla f(x_0) = (2, 1)^T - \\frac{1}{4}(4, 4)^T = (1, 0)^T$.",
            ],
            "final_answer": "$x_1 = (1, 0)^T$",
        },
        "questions": [
            {
                "id": "q_ocd_1",
                "type": "mcq",
                "prompt": "Para la función cuadrática convexa $f(x) = \\frac{1}{2} x^T Q x$ donde $Q \\succ 0$ tiene valores propios $\\lambda_{\\min} = 1$ y $\\lambda_{\\max} = 10$, ¿para qué rango de tasa de aprendizaje $\\eta > 0$ converge el descenso de gradiente $x_{k+1} = (I - \\eta Q)x_k$?",
                "options": [
                    "$0 < \\eta < \\frac{1}{5}$",
                    "$0 < \\eta < 2$",
                    "$0 < \\eta < 10$",
                    "$\\eta > \\frac{1}{10}$",
                ],
                "correct_index": 0,
                "hint": "Necesitas que $|1 - \\eta \\lambda_i| < 1$ para todos los valores propios, en particular para $\\lambda_{\\max} = 10$, es decir $\\eta < 2 / \\lambda_{\\max}$.",
                "explanation": "La iteración converge si y solo si el radio espectral de $(I - \\eta Q)$ es menor que 1, lo que exige $0 < \\eta < \\frac{2}{\\lambda_{\\max}} = \\frac{2}{10} = \\frac{1}{5}$.",
            }
        ],
    },

    # ==========================================
    # SEMESTRE 4 (ANTICIPACIÓN): MODELOS PROBABILÍSTICOS (MP)
    # ==========================================
    {
        "id": "mp_bayes_variables_aleatorias",
        "title": "Probabilidad Condicional, Teorema de Bayes, Esperanza y Varianza",
        "course_id": "MP",
        "semester": 4,
        "domain": "prob_est",
        "xp": 15,
        "estimated_mins": 12,
        "prereqs": ["tme_combinatoria_descriptiva", "c1_integracion_tfc"],
        "encompasses": {"tme_combinatoria_descriptiva": 0.8, "c1_integracion_tfc": 0.65},
        "generator_type": "bayes_theorem",
        "theory": (
            "- **Teorema de Bayes** (con partición $B_1, \\dots, B_k$):\n"
            "$$\\mathbb{P}(B_j \\mid A) = \\frac{\\mathbb{P}(A \\mid B_j)\\,\\mathbb{P}(B_j)}{\\sum_{i=1}^k \\mathbb{P}(A \\mid B_i)\\,\\mathbb{P}(B_i)}$$\n"
            "- **Esperanza y Varianza**:\n"
            "  $\\mathbb{E}[aX + bY + c] = a\\mathbb{E}[X] + b\\mathbb{E}[Y] + c$ (**siempre**, aun sin independencia).\n"
            "  $\\text{Var}(X) = \\mathbb{E}[X^2] - (\\mathbb{E}[X])^2$, y $\\text{Var}(aX + bY) = a^2\\text{Var}(X) + b^2\\text{Var}(Y) + 2ab\\,\\text{Cov}(X,Y)$."
        ),
        "ds_connection": (
            "El Teorema de Bayes es la base de los clasificadores **Naive Bayes**, el filtrado de spam, la estimación MAP (Maximum A Posteriori) "
            "y todo el curso de **Métodos Bayesianos** del Semestre 7 de tu carrera."
        ),
        "uc_exam_tip": (
            "En problemas de densidades continuas $f_X(x) = c x^k$ en $[a, b]$, el primer paso **siempre** es encontrar la constante de normalización $c$ "
            "imponiendo $\\int_{-\\infty}^{\\infty} f_X(x)\\,dx = 1$."
        ),
        "worked_example": {
            "problem": "Un modelo detector de fraude tiene sensibilidad $\\mathbb{P}(+\\mid F) = 0.90$, tasa de falsos positivos $\\mathbb{P}(+\\mid F^c) = 0.05$, y la tasa base de fraude es $\\mathbb{P}(F) = 0.02$. Si una transacción da positivo ($+$), ¿cuál es $\\mathbb{P}(F \\mid +)$?",
            "steps": [
                "Por Probabilidad Total: $\\mathbb{P}(+) = \\mathbb{P}(+\\mid F)\\mathbb{P}(F) + \\mathbb{P}(+\\mid F^c)\\mathbb{P}(F^c) = 0.90(0.02) + 0.05(0.98) = 0.018 + 0.049 = 0.067$.",
                "Por Teorema de Bayes: $\\mathbb{P}(F \\mid +) = \\frac{0.018}{0.067} = \\frac{18}{67} \\approx 0.2687$.",
            ],
            "final_answer": "$\\frac{18}{67} \\approx 26.9\\%$",
        },
        "questions": [
            {
                "id": "q_mp_1",
                "type": "mcq",
                "prompt": "Sean $X$ e $Y$ variables aleatorias independientes con $\\text{Var}(X) = 4$ y $\\text{Var}(Y) = 9$. ¿Cuánto vale $\\text{Var}(2X - Y + 5)$?",
                "options": ["$25$", "$7$", "$-1$", "$30$"],
                "correct_index": 0,
                "hint": "Por independencia $\\text{Cov}(X, Y) = 0$, y recuerda que $\\text{Var}(aX + bY + c) = a^2\\text{Var}(X) + b^2\\text{Var}(Y)$.",
                "explanation": "Al ser independientes, $\\text{Var}(2X - Y + 5) = 2^2 \\text{Var}(X) + (-1)^2 \\text{Var}(Y) + 0 = 4(4) + 1(9) = 25$. (¡El signo menos se eleva al cuadrado!).",
            }
        ],
    },
    {
        "id": "mp_vectores_aleatorios_tcl",
        "title": "Matriz de Covarianza, Ley de Grandes Números y Teorema Central del Límite",
        "course_id": "MP",
        "semester": 4,
        "domain": "prob_est",
        "xp": 16,
        "estimated_mins": 13,
        "prereqs": ["mp_bayes_variables_aleatorias", "alam_svd_pca"],
        "encompasses": {"mp_bayes_variables_aleatorias": 0.85, "alam_svd_pca": 0.6},
        "generator_type": "clt_sample_mean",
        "theory": (
            "- Para un vector aleatorio $X \\in \\mathbb{R}^d$ con matriz de covarianza $\\Sigma_X$ y una transformación afín $Y = A X + b$, se cumple:\n"
            "$$\\mathbb{E}[Y] = A\\,\\mathbb{E}[X] + b, \\qquad \\Sigma_Y = A\\,\\Sigma_X\\,A^T$$\n"
            "- **Teorema Central del Límite (TCL)**: Si $X_1, \\dots, X_n$ son i.i.d. con media $\\mu$ y varianza $\\sigma^2 < \\infty$, entonces la media muestral $\\bar{X}_n = \\frac{1}{n}\\sum_{i=1}^n X_i$ verifica:\n"
            "$$\\frac{\\bar{X}_n - \\mu}{\\sigma / \\sqrt{n}} \\xrightarrow{d} \\mathcal{N}(0, 1) \\quad \\text{cuando } n \\to \\infty$$"
        ),
        "ds_connection": (
            "La fórmula $\\Sigma_Y = A \\Sigma_X A^T$ une Álgebra Lineal con Estadística Multivariada (filtros de Kalman, Gaussianas Multivariadas, Whitening), "
            "y el TCL justifica los intervalos de confianza, los A/B tests en producto y la reducción del error estándar a razón de $1/\\sqrt{n}$."
        ),
        "uc_exam_tip": (
            "Nota que para reducir a la mitad el margen de error estándar $\\sigma / \\sqrt{n}$ del promedio muestral $\\bar{X}_n$, "
            "debes **cuadruplicar** el tamaño muestral $n$ (porque aparece $\\sqrt{n}$ en el denominador)."
        ),
        "worked_example": {
            "problem": "Si $X_1, \\dots, X_{100}$ son i.i.d. con $\\mu = 50$ y $\\sigma = 10$, determine la media y la desviación estándar de $\\bar{X}_{100}$.",
            "steps": [
                "La esperanza de la media muestral es insesgada: $\\mathbb{E}[\\bar{X}_{100}] = \\mu = 50$.",
                "La varianza de la media muestral es $\\text{Var}(\\bar{X}_{100}) = \\frac{\\sigma^2}{n} = \\frac{100}{100} = 1$.",
                "Por tanto, la desviación estándar (error estándar) es $\\sigma_{\\bar{X}} = \\frac{\\sigma}{\\sqrt{n}} = \\frac{10}{\\sqrt{100}} = 1$.",
            ],
            "final_answer": "$\\mathbb{E}[\\bar{X}_{100}] = 50,\\quad \\text{SD}(\\bar{X}_{100}) = 1$",
        },
        "questions": [
            {
                "id": "q_mp_tcl_1",
                "type": "mcq",
                "prompt": "Si el vector aleatorio $X = (X_1, X_2)^T$ tiene matriz de covarianza $\\Sigma_X = \\begin{pmatrix} 2 & 1 \\\\ 1 & 2 \\end{pmatrix}$ y definimos $Y = X_1 - X_2$, ¿cuánto vale $\\text{Var}(Y)$?",
                "options": ["$2$", "$4$", "$6$", "$0$"],
                "correct_index": 0,
                "hint": "Escribe $Y = a^T X$ con $a = (1, -1)^T$, entonces $\\text{Var}(Y) = a^T \\Sigma_X a = \\text{Var}(X_1) + \\text{Var}(X_2) - 2\\text{Cov}(X_1, X_2)$.",
                "explanation": "Usando $\\text{Var}(X_1 - X_2) = \\text{Var}(X_1) + \\text{Var}(X_2) - 2\\text{Cov}(X_1, X_2) = 2 + 2 - 2(1) = 2$.",
            }
        ],
    },
]
