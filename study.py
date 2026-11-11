"""Transiciones de estudio y selección local del quiz del piloto."""

import hashlib
import random
import uuid

import diagnostic
from generators import generate_parametric_questions


LESSON_TASKS = {
    "lesson", "review", "recovery", "prerequisite_check", "anticipation", "practice", "quiz_review",
}
DIRECT_TASKS = {"review", "prerequisite_check", "quiz_review"}
MIN_QUIZ_TOPICS = 2


def empty_state():
    return {
        "lessons": {}, "last_lesson": None, "quiz": None, "seen": [], "quiz_reviews": {},
        "first_attempts": [],
    }


def prompt_key(prompt):
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def diagnostic_keys(session):
    if session is None:
        return set()
    keys = set(session.get("previous_prompts", []))
    answers = session["answers"]
    for index in range(len(answers) + 1):
        item = diagnostic.next_question(session["seed"], answers[:index])
        if item is not None:
            keys.add(prompt_key(item["question"]["prompt"]))
    return keys


def eligible_topics(states, progress, diagnostic_session):
    directly_assessed = {
        item["topic_id"] for item in (diagnostic_session or {}).get("answers", [])
        if item["choice"] is not None
    }
    practiced = {
        session["topic"]["id"] for session in progress["lessons"].values()
        if session["answers"]
    }
    return [
        tid for tid in diagnostic.TOPICS_BY_ID
        if states[tid]["total_attempts"] or states[tid]["mastery"] >= 0.75
        or tid in directly_assessed or tid in practiced
    ]


def new_lesson(topic, task_type):
    return {
        "id": uuid.uuid4().hex,
        "topic": topic,
        "task_type": task_type,
        "step": int(task_type in DIRECT_TASKS),
        "answers": [],
        "hint_used": False,
        "result": None,
    }


def lesson_overview(session, slot):
    return {
        "id": session["id"],
        "slot": slot,
        "topic_id": session["topic"]["id"],
        "task_type": session["task_type"],
        "answered": len(session["answers"]),
        "total": len(session["topic"]["questions"]),
    }


def advance_lesson(progress, session, body, now_ts):
    """Devuelve si corresponde registrar el resultado tras la última corrección."""
    if (session["result"] is not None or session["id"] != body.get("session_id")
            or session["step"] != body.get("step") or len(session["answers"]) != body.get("answered")):
        return False
    step = session["step"]
    answers = session["answers"]
    questions = session["topic"]["questions"]
    tracks_hint = body.get("tracks_hint") is True
    waiting_for_answer = 0 < step <= len(questions) and len(answers) == step - 1
    if body["action"] == "hint":
        if waiting_for_answer and session["task_type"] not in DIRECT_TASKS:
            session["hint_used"] = True
        return False
    if "choice" in body:
        if waiting_for_answer:
            task_type = session["task_type"]
            hint_used = session.get("hint_used")
            if task_type in DIRECT_TASKS:
                hint_used = False
            elif hint_used is False and not tracks_hint:
                # Un cliente anterior podía mostrar la pista sin avisar al servidor.
                hint_used = None
            confirm_answer(
                progress, session, questions[step - 1], body["choice"], now_ts,
                topic_id=session["topic"]["id"], task_type=task_type, hint_used=hint_used,
            )
        return False
    if step != len(answers):
        raise ValueError("Confirma la respuesta para continuar.")
    if step == len(questions):
        return True
    session["step"] += 1
    session["hint_used"] = False if tracks_hint else None
    return False


def valid_choice(choice, question):
    if type(choice) is not int or not 0 <= choice < len(question["options"]):
        raise ValueError("Selecciona una alternativa válida.")
    return choice


def confirm_answer(progress, session, question, choice, now_ts, *, topic_id, task_type, hint_used):
    choice = valid_choice(choice, question)
    question_index = len(session["answers"])
    session["answers"].append(choice)
    progress.setdefault("first_attempts", []).append({
        "session_id": session["id"],
        "topic_id": topic_id,
        "task_type": task_type,
        "question_index": question_index,
        "prompt_key": prompt_key(question["prompt"]),
        "correct": choice == question["correct_index"],
        "hint_used": hint_used,
        "answered_ts": now_ts,
    })


def quiz_question(variant):
    topic = diagnostic.TOPICS_BY_ID[variant["topic_id"]]
    rng = random.Random(variant["seed"])
    return generate_parametric_questions(topic["generator_type"], count=1, rng=rng)[0]


def new_quiz(eligible, seen, seed):
    if len(eligible) < MIN_QUIZ_TOPICS:
        raise ValueError("Responde problemas de al menos dos temas del piloto para iniciar el quiz.")
    rng = random.Random(seed)
    topics = list(eligible)
    rng.shuffle(topics)
    variants = []
    for topic_id in topics:
        for _ in range(512):
            variant = {"topic_id": topic_id, "seed": rng.getrandbits(32)}
            key = prompt_key(quiz_question(variant)["prompt"])
            if key not in seen:
                seen.add(key)
                variants.append(variant)
                break
    if len(variants) < MIN_QUIZ_TOPICS:
        raise ValueError("Se necesitan variantes inéditas en al menos dos temas para armar otro quiz.")
    return {"id": uuid.uuid4().hex, "variants": variants, "answers": []}


def quiz_overview(session, eligible):
    if session is None:
        return {"status": "idle", "eligible": eligible}
    answered, total = len(session["answers"]), len(session["variants"])
    return {
        "id": session["id"], "answered": answered, "total": total, "eligible": eligible,
        "status": "completed" if answered == total else "in_progress",
    }


def quiz_results(session):
    results = []
    for variant, choice in zip(session["variants"], session["answers"]):
        topic_id = variant["topic_id"]
        question = quiz_question(variant)
        results.append({
            "topic_id": topic_id,
            "title": diagnostic.TOPICS_BY_ID[topic_id]["title"],
            "prompt": question["prompt"],
            "chosen": question["options"][choice],
            "correct_answer": question["options"][question["correct_index"]],
            "correct": choice == question["correct_index"],
            "explanation": question["explanation"],
        })
    return results


def public_quiz(session, eligible):
    overview = quiz_overview(session, eligible)
    if overview["status"] == "in_progress":
        question = quiz_question(session["variants"][overview["answered"]])
        overview["question"] = {key: question[key] for key in ("prompt", "options")}
    elif overview["status"] == "completed":
        overview["results"] = quiz_results(session)
        overview["xp_earned"] = sum(item["correct"] for item in overview["results"])
    return overview
