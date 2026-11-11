"""Selección de preguntas y evidencia del diagnóstico del piloto MAT1107."""

import random

from curriculum import TOPICS
from generators import generate_parametric_questions


PILOT_TOPIC_IDS = {"ic_desigualdades", "ic_funciones", "ic_limites", "ic_continuidad_derivada"}
TOPICS_BY_ID = {topic["id"]: topic for topic in TOPICS if topic["id"] in PILOT_TOPIC_IDS}
START_TOPIC = "ic_funciones"
QUESTION_LIMIT = 6
INITIAL_MASTERY = 0.75
INITIAL_REVIEW_DAYS = 2.0


def _ancestors(topic_id):
    result = set()
    for prereq in TOPICS_BY_ID[topic_id]["prereqs"]:
        if prereq in TOPICS_BY_ID:
            result.add(prereq)
            result.update(_ancestors(prereq))
    return result


ANCESTORS = {tid: _ancestors(tid) for tid in TOPICS_BY_ID}


def evidence(answers):
    """Una omisión no cuenta como acierto ni como error."""
    summary = []
    for tid, topic in TOPICS_BY_ID.items():
        direct = [answer for answer in answers if answer["topic_id"] == tid]
        correct = sum(answer["correct"] is True for answer in direct)
        incorrect = sum(answer["correct"] is False for answer in direct)
        positive = list(dict.fromkeys(
            answer["topic_id"] for answer in answers
            if answer["correct"] is True and tid in ANCESTORS[answer["topic_id"]]
        ))
        negative = list(dict.fromkeys(
            answer["topic_id"] for answer in answers
            if answer["correct"] is False and answer["topic_id"] in ANCESTORS[tid]
        ))
        if correct or incorrect:
            kind = "direct"
        elif positive or negative:
            kind = "inferred"
        else:
            kind = "unassessed"
        summary.append({
            "topic_id": tid,
            "topic_title": topic["title"],
            "kind": kind,
            "correct": correct,
            "incorrect": incorrect,
            "skipped": len(direct) - correct - incorrect,
            "positive_from": positive,
            "negative_from": negative,
        })
    return summary


def next_question(seed, answers):
    if len(answers) >= QUESTION_LIMIT:
        return None
    tid, reason = _next_topic(answers)
    if tid is None:
        return None
    topic = TOPICS_BY_ID[tid]
    # Las dos preguntas para un mismo tema usan familias distintas.
    attempt = sum(answer["topic_id"] == tid for answer in answers)
    rng = random.Random(f"{seed}:{tid}")
    question = generate_parametric_questions(topic["generator_type"], count=2, rng=rng)[attempt]
    return {"topic_id": tid, "topic_title": topic["title"], "reason": reason, "question": question}


def record_answer(session, choice, now_ts):
    item = session["current"]
    if item is None:
        raise ValueError("El diagnóstico ya terminó.")
    question = item["question"]
    if choice is not None and (type(choice) is not int or not 0 <= choice < len(question["options"])):
        raise ValueError("Selecciona una alternativa válida.")
    answers = session["answers"] + [{
        "topic_id": item["topic_id"],
        "choice": choice,
        "correct": None if choice is None else choice == question["correct_index"],
        "answered_at": now_ts,
    }]
    return {**session, "answers": answers, "current": next_question(session["seed"], answers)}


def backup_session(session):
    if session is None:
        return None
    return {
        "id": session["id"],
        "seed": session["seed"],
        "previous_prompts": session.get("previous_prompts", []),
        "answers": [
            {"choice": answer["choice"], "answered_at": answer["answered_at"]}
            for answer in session["answers"]
        ],
    }


def restore_session(snapshot):
    if snapshot is None:
        return None
    seed = snapshot["seed"]
    session = {
        "id": snapshot["id"], "seed": seed, "answers": [],
        "current": next_question(seed, []), "previous_prompts": snapshot.get("previous_prompts", []),
    }
    for answer in snapshot["answers"]:
        session = record_answer(session, answer["choice"], float(answer["answered_at"]))
    return session


def _next_topic(answers):
    if not answers:
        return START_TOPIC, "initial"

    last = answers[-1]
    tid = last["topic_id"]
    asked = {answer["topic_id"] for answer in answers}
    if last["correct"] is True:
        for successor, topic in TOPICS_BY_ID.items():
            if tid in topic["prereqs"] and successor not in asked:
                return successor, "successor"
    else:
        for prereq in TOPICS_BY_ID[tid]["prereqs"]:
            if prereq in TOPICS_BY_ID and prereq not in asked:
                return prereq, "prerequisite"

    for item in evidence(answers):
        if not item["positive_from"]:
            continue
        candidate = item["topic_id"]
        if candidate not in asked:
            return candidate, "confirm_inference"
        if item["incorrect"] == 1 and item["correct"] == 0 and item["skipped"] == 0:
            return candidate, "resolve_conflict"
    return None, None


def public_session(session):
    if session is None:
        return {"status": "idle", "max_questions": QUESTION_LIMIT}
    answers = session["answers"]
    item = session["current"]
    response = {
        "status": "in_progress" if item else "completed",
        "session_id": session["id"],
        "answered": len(answers),
        "max_questions": QUESTION_LIMIT,
    }
    if item:
        question = item["question"]
        response["item"] = {
            "topic_id": item["topic_id"],
            "topic_title": item["topic_title"],
            "reason": item["reason"],
            "question": {"prompt": question["prompt"], "options": question["options"]},
        }
    else:
        response["evidence"] = evidence(answers)
    return response
