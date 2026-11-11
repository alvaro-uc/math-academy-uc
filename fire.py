"""Crédito de repaso basado en operaciones auditadas de cada ejercicio."""

DAY = 86400.0

# Cada entrada contiene solo aristas observables en esa familia. El peso
# representa la parte de un repaso directo que aporta la operación.
AUDITS = {
    "limite_factorizado": (
        "ic_limites",
        {
            "ic_limites": {
                "ic_desigualdades": (0.50, "Factorizar el polinomio de la fracción racional."),
            },
        },
    ),
    "derivada_por_definicion": (
        "ic_continuidad_derivada",
        {
            "ic_continuidad_derivada": {
                "ic_limites": (0.50, "Simplificar y calcular el límite del cociente incremental."),
            },
        },
    ),
    "extension_radical": (
        "ic_continuidad_derivada",
        {
            "ic_continuidad_derivada": {
                "ic_limites": (0.60, "Calcular el límite de la expresión simplificada."),
                "ic_funciones": (0.60, "Hallar el dominio natural de la composición."),
            },
            "ic_limites": {
                "ic_desigualdades": (0.50, "Factorizar y verificar el signo cerca del empalme."),
            },
            "ic_funciones": {
                "ic_desigualdades": (0.75, "Resolver la condición de signo del radicando."),
            },
        },
    ),
}


def question_evidence(topic_id, question):
    audit = AUDITS.get(question.get("fire_audit"))
    if audit is None or audit[0] != topic_id:
        return {}
    _, edges = audit
    best = {}
    pending = [(topic_id, 1.0, [topic_id], [])]
    while pending:
        source, weight, path, operations = pending.pop()
        for target, (fraction, operation) in edges.get(source, {}).items():
            combined = weight * fraction
            if target in path or combined <= best.get(target, {}).get("weight", 0.0):
                continue
            evidence = {
                "question_id": question["id"],
                "audit": question["fire_audit"],
                "weight": combined,
                "path": [*path, target],
                "operations": [*operations, operation],
            }
            best[target] = evidence
            pending.append((target, combined, evidence["path"], evidence["operations"]))
    return best


def review_evidence(topic_id, questions, answers):
    """Cuenta una vez cada enunciado acertado y cada destino de ese enunciado."""
    evidence = {}
    seen = set()
    for question, choice in zip(questions, answers, strict=True):
        prompt = question["prompt"]
        if prompt in seen:
            continue
        seen.add(prompt)
        if choice == question["correct_index"]:
            for target, item in question_evidence(topic_id, question).items():
                evidence.setdefault(target, []).append(item)
    return evidence


def extended_schedule(state, dose, now_ts):
    """Aplaza un repaso existente con una fracción del intervalo ya transcurrido."""
    last = state["last_practiced_ts"]
    if state["mastery"] < 0.75 or state["repetitions"] <= 0 or last is None:
        return None
    stability = float(state["stability_days"])
    elapsed = max(0.0, (now_ts - last) / DAY)
    updated = min(90.0, stability + dose * min(elapsed, stability))
    next_review = last + updated * DAY
    previous = state["next_review_ts"]
    if previous is None:
        previous = last + stability * DAY
    if updated <= stability or next_review <= previous:
        return None
    return updated, next_review, (next_review - previous) / DAY
