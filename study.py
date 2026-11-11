"""Transiciones de estudio y selección local del quiz del piloto."""

import hashlib
import random
import uuid
from collections import Counter, defaultdict

import diagnostic
from generators import generate_parametric_questions


RETENTION_TASKS = {"retention_7d": 7, "retention_14d": 14}
DAY_SECONDS = 86400
LESSON_TASKS = {
    "lesson", "review", "recovery", "prerequisite_check", "anticipation", "practice", "quiz_review",
} | RETENTION_TASKS.keys()
DIRECT_TASKS = {"review", "prerequisite_check", "quiz_review"} | RETENTION_TASKS.keys()
INDEPENDENT_TASKS = DIRECT_TASKS | {"quiz"}
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
                active_ms=body.get("active_ms"),
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


def confirm_answer(progress, session, question, choice, now_ts, *, topic_id, task_type, hint_used, active_ms):
    choice = valid_choice(choice, question)
    if not valid_active_ms(active_ms):
        raise ValueError("La duración de la respuesta no es válida.")
    question_index = len(session["answers"])
    session["answers"].append(choice)
    progress.setdefault("first_attempts", []).append({
        "session_id": session["id"],
        "topic_id": topic_id,
        "task_type": task_type,
        "question_index": question_index,
        "prompt_key": prompt_key(question["prompt"]),
        "family": question.get("family"),
        "correct": choice == question["correct_index"],
        "hint_used": hint_used,
        "active_ms": active_ms,
        "answered_ts": now_ts,
    })


def valid_active_ms(value):
    return value is None or (type(value) is int and 0 <= value <= 2**53 - 1)


def valid_attempt(item):
    if not isinstance(item, dict):
        return False
    timestamp = item.get("answered_ts")
    index = item.get("question_index")
    family = item.get("family")
    hint = item.get("hint_used")
    return (
        all(isinstance(item.get(key), str) for key in ("session_id", "topic_id", "task_type", "prompt_key"))
        and type(index) is int and index >= 0
        and type(timestamp) in (int, float) and -8.64e12 <= timestamp <= 8.64e12
        and type(item.get("correct")) is bool
        and (hint is None or type(hint) is bool)
        and (family is None or isinstance(family, str))
        and valid_active_ms(item.get("active_ms"))
    )


def retention_anchor(attempts):
    return next((item for item in attempts if item["task_type"] not in RETENTION_TASKS), None)


def retention_result(progress, lesson, correct):
    topic_id = lesson["topic"]["id"]
    attempts = [item for item in progress["first_attempts"] if item["topic_id"] == topic_id]
    anchor = retention_anchor(attempts)
    return {
        "correct": correct,
        "total": len(lesson["answers"]),
        "intervening_attempts": sum(item["session_id"] != lesson["id"] for item in attempts[attempts.index(anchor) + 1:]),
    }


def learning_overview(progress, xp_logs, now_ts):
    by_topic = defaultdict(list)
    measured = set()
    for item in progress.get("first_attempts", []):
        by_topic[item["topic_id"]].append(item)
        measured.add((item["session_id"], item["question_index"]))

    undated = Counter()
    pending_results = set()
    for lesson in progress["lessons"].values():
        undated[lesson["topic"]["id"]] += sum(
            (lesson["id"], index) not in measured for index in range(len(lesson["answers"]))
        )
        if lesson["task_type"] in RETENTION_TASKS and lesson["result"] is None:
            pending_results.add(lesson["id"])
    quiz = progress["quiz"]
    if quiz:
        if len(quiz["answers"]) < len(quiz["variants"]):
            pending_results.add(quiz["id"])
        for index, variant in enumerate(quiz["variants"][:len(quiz["answers"])]):
            if (quiz["id"], index) not in measured:
                undated[variant["topic_id"]] += 1

    last_session = {}
    for log in xp_logs:
        if log["task_type"] in LESSON_TASKS:
            topic_id = log["topic_id"]
            last_session[topic_id] = max(last_session.get(topic_id, log["created_ts"]), log["created_ts"])

    topics = {}
    for topic_id in by_topic.keys() | last_session.keys() | {tid for tid in undated if undated[tid]}:
        attempts = by_topic[topic_id]
        last_answer = max((item["answered_ts"] for item in attempts), default=None)
        anchor = retention_anchor(attempts)
        topics[topic_id] = {
            "last_practice_ts": last_answer if last_answer is not None else last_session.get(topic_id),
            "legacy_date": last_answer is None and topic_id in last_session,
            "undated": undated[topic_id],
            "windows": {
                days: learning_counts(
                    (item for item in attempts if now_ts - days * DAY_SECONDS <= item["answered_ts"] <= now_ts),
                    pending_results,
                )
                for days in RETENTION_TASKS.values()
            },
            "controls": [
                control_overview(progress, topic_id, task_type, anchor["answered_ts"], now_ts)
                for task_type in RETENTION_TASKS
            ] if anchor and topic_id in diagnostic.PILOT_TOPIC_IDS else [],
        }
    return topics


def learning_counts(attempts, pending_results):
    counts = {"answered": 0, "independent": 0, "correct_independent": 0, "timed": 0, "active_ms": 0, "family_missing": 0}
    for item in attempts:
        counts["answered"] += 1
        if (item["session_id"] not in pending_results and item.get("hint_used") is False
                and item["task_type"] in INDEPENDENT_TASKS):
            counts["independent"] += 1
            counts["correct_independent"] += int(item["correct"])
        if item.get("active_ms") is not None:
            counts["timed"] += 1
            counts["active_ms"] += item["active_ms"]
        counts["family_missing"] += int(not item.get("family"))
    return counts


def control_overview(progress, topic_id, task_type, anchor_ts, now_ts):
    days = RETENTION_TASKS[task_type]
    due_ts = anchor_ts + days * DAY_SECONDS
    lesson = progress["lessons"].get(f"{topic_id}:{task_type}")
    control = {"task_type": task_type, "days": days, "due_ts": due_ts}
    if lesson:
        return {
            **control, "status": "completed" if lesson["result"] else "in_progress",
            "result": lesson["result"], "started_ts": lesson["retention_started_ts"],
            "elapsed_days": (lesson["retention_started_ts"] - anchor_ts) // DAY_SECONDS,
        }
    return {**control, "status": "available" if now_ts >= due_ts else "pending"}


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
