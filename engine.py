# -*- coding: utf-8 -*-
"""
Motor Pedagógico FIRe (Fractional Implicit Repetition) + SQLite Local
Inspirado en la arquitectura de Math Academy para la Licenciatura en Ingeniería
en Ciencia de Datos UC.
"""

import datetime
import json
import math
import os
import random
import sqlite3
import uuid

import diagnostic
import fire
import study
from curriculum import COURSES, TOPICS
from generators import gen_continuous_radical_extension, generate_parametric_questions

import urllib.request


def _load_dotenv():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

_DEFAULT_DATA_DIR = (
    "/tmp/math_academy_data"
    if os.environ.get("VERCEL")
    else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
)
DB_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join(_DEFAULT_DATA_DIR, "math_academy.db"))

TOPICS_BY_ID = {t["id"]: t for t in TOPICS}
COURSES_BY_ID = {c["id"]: c for c in COURSES}
PASS_SCORE = 0.65
RECOVERY_FAILURES = 2
RECOVERY_INTERVAL_DAYS = 1.0
DIRECT_RETRIEVAL_TASKS = study.DIRECT_TASKS


class _TursoCursor:
    """Adaptador sin dependencias externas para Turso (libSQL HTTP Pipeline API)."""

    def __init__(self, url, token):
        self.url = url.replace("libsql://", "https://").rstrip("/") + "/v2/pipeline"
        self.token = token
        self._rows = []

    def _convert_arg(self, v):
        if v is None:
            return {"type": "null"}
        if isinstance(v, int):
            return {"type": "integer", "value": str(v)}
        if isinstance(v, float):
            return {"type": "float", "value": v}
        return {"type": "text", "value": str(v)}

    def _parse_cell(self, c):
        t = c.get("type")
        if t == "null":
            return None
        if t == "integer":
            return int(c["value"])
        if t == "float":
            return float(c["value"])
        return c.get("value")

    def _statement(self, sql, params):
        stmt = {"sql": sql}
        if params:
            stmt["args"] = [self._convert_arg(p) for p in params]
        return stmt

    def _request(self, request):
        payload = json.dumps({"requests": [request, {"type": "close"}]}).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        res0 = data.get("results", [{}])[0]
        if res0.get("type") == "error":
            raise RuntimeError(res0.get("error", {}).get("message", "Turso SQL error"))
        return res0.get("response", {}).get("result", {})

    def execute(self, sql, params=()):
        exec_res = self._request({"type": "execute", "stmt": self._statement(sql, params)})
        cols = [c["name"] for c in exec_res.get("cols", [])]
        self._rows = [
            {cols[i]: self._parse_cell(row[i]) for i in range(len(cols))}
            for row in exec_res.get("rows", [])
        ]
        return self

    def write_batch(self, statements):
        steps = [{"stmt": {"sql": "BEGIN IMMEDIATE"}}]
        for sql, params in [*statements, ("COMMIT", ())]:
            steps.append({
                "condition": {"type": "ok", "step": len(steps) - 1},
                "stmt": self._statement(sql, params),
            })
        result = self._request({"type": "batch", "batch": {"steps": steps}})
        for error in result["step_errors"]:
            if error:
                raise RuntimeError(error["message"])

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class _TursoConn:
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def cursor(self):
        return _TursoCursor(self.url, self.token)

    def commit(self):
        pass

    def close(self):
        pass


class _PostgresCursorWrapper:
    """Convierte placeholders '?' de SQLite y expresiones menores a sintaxis PostgreSQL."""

    def __init__(self, real_cur):
        self._cur = real_cur

    def execute(self, sql, params=()):
        pg_sql = sql.replace("?", "%s")
        pg_sql = pg_sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        pg_sql = pg_sql.replace("MAX(repetitions, 1)", "GREATEST(repetitions, 1)")
        pg_sql = pg_sql.replace("MAX(total_xp, 45)", "GREATEST(total_xp, 45)")
        pg_sql = pg_sql.replace("MAX(total_xp, 100)", "GREATEST(total_xp, 100)")
        if "INSERT OR IGNORE INTO topic_state" in pg_sql:
            pg_sql = pg_sql.replace(
                "INSERT OR IGNORE INTO topic_state", "INSERT INTO topic_state"
            )
            pg_sql = pg_sql.rstrip().rstrip(";") + " ON CONFLICT (topic_id) DO NOTHING"
        self._cur.execute(pg_sql, params)
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        return [dict(r) for r in self._cur.fetchall()]


class _PostgresConnWrapper:
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        import psycopg2.extras

        return _PostgresCursorWrapper(
            self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        )

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_storage_backend_name():
    if os.environ.get("TURSO_DATABASE_URL") and os.environ.get("TURSO_AUTH_TOKEN"):
        return "turso-cloud"
    if os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL"):
        return "postgres-cloud"
    return "sqlite-local"


def get_conn():
    turso_url = os.environ.get("TURSO_DATABASE_URL")
    turso_token = os.environ.get("TURSO_AUTH_TOKEN")
    if turso_url and turso_token:
        return _TursoConn(turso_url, turso_token)

    pg_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if pg_url:
        import psycopg2

        return _PostgresConnWrapper(psycopg2.connect(pg_url))

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL DEFAULT 'Estudiante Ingeniería en Ciencia de Datos UC',
            current_semester INTEGER NOT NULL DEFAULT 1,
            daily_goal_xp INTEGER NOT NULL DEFAULT 30,
            total_xp INTEGER NOT NULL DEFAULT 0,
            streak_days INTEGER NOT NULL DEFAULT 1,
            last_active_date TEXT,
            diagnostic_completed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS topic_state (
            topic_id TEXT PRIMARY KEY,
            mastery REAL NOT NULL DEFAULT 0.0,
            stability_days REAL NOT NULL DEFAULT 2.0,
            repetitions INTEGER NOT NULL DEFAULT 0,
            last_practiced_ts REAL,
            next_review_ts REAL,
            total_attempts INTEGER NOT NULL DEFAULT 0,
            correct_attempts INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS xp_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_str TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            xp_earned INTEGER NOT NULL,
            score_ratio REAL NOT NULL,
            implicit_topics_json TEXT NOT NULL,
            created_ts REAL NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS diagnostic_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            session_json TEXT,
            preset_mode TEXT,
            revision DOUBLE PRECISION NOT NULL DEFAULT 0
        )
        """
    )
    cur.execute("INSERT INTO diagnostic_state (id) VALUES (1) ON CONFLICT (id) DO NOTHING")
    cur.execute(
        """CREATE TABLE IF NOT EXISTS study_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            data_json TEXT NOT NULL,
            revision DOUBLE PRECISION NOT NULL DEFAULT 0
        )"""
    )
    cur.execute(
        "INSERT INTO study_state (id, data_json) VALUES (1, ?) ON CONFLICT (id) DO NOTHING",
        (json.dumps(study.empty_state()),),
    )
    cur.execute(
        """
        INSERT INTO user_profile (id, name, daily_goal_xp)
        VALUES (1, 'Estudiante Lic. Ingeniería en Ciencia de Datos UC', 35)
        ON CONFLICT (id) DO NOTHING
        """
    )
    for t in TOPICS:
        cur.execute(
            """
            INSERT OR IGNORE INTO topic_state (topic_id, mastery, stability_days, repetitions, last_practiced_ts, next_review_ts)
            VALUES (?, 0.0, 2.0, 0, NULL, NULL)
            """,
            (t["id"],),
        )
    conn.commit()
    conn.close()


def compute_retention(row, now_ts=None):
    """Calcula la retención de memoria R(t) = 0.78^(Δt / S) y el estado de repaso del nodo."""
    if now_ts is None:
        now_ts = datetime.datetime.now().timestamp()
    mastery = float(row.get("mastery", 0.0))
    last_ts = row.get("last_practiced_ts")
    stability = max(0.5, float(row.get("stability_days", 2.0)))
    reps = int(row.get("repetitions", 0))

    if reps == 0 or last_ts is None or mastery <= 0.05:
        return {
            "retention": 0.0,
            "days_elapsed": 0.0,
            "due_for_review": False,
        }

    days_elapsed = max(0.0, (now_ts - float(last_ts)) / 86400.0)
    # R(t) comienza en 1.0 tras practicar (Δt = 0) y alcanza el umbral 0.78 en Δt = S (next_review_ts)
    retention = math.pow(0.78, days_elapsed / stability)
    if row.get("next_review_ts") is not None:
        due = mastery >= 0.75 and now_ts >= float(row["next_review_ts"])
    else:
        due = mastery >= 0.75 and retention <= 0.78
    return {
        "retention": round(min(1.0, max(0.0, retention)), 3),
        "days_elapsed": round(days_elapsed, 4),
        "due_for_review": bool(due),
    }


def _review_history(xp_logs):
    failures = {}
    last_pass = {}
    failed_checks = {}
    for index, row in enumerate(xp_logs):
        topic_id = row["topic_id"]
        task_type = row["task_type"]
        if topic_id not in TOPICS_BY_ID or task_type == "diagnostic":
            continue
        if row["score_ratio"] >= PASS_SCORE:
            last_pass[topic_id] = index
            failures.pop(topic_id, None)
        elif task_type == "review":
            count, _ = failures.get(topic_id, (0, -1))
            failures[topic_id] = (count + 1, index)
        elif task_type == "prerequisite_check":
            failed_checks[topic_id] = index
    return failures, last_pass, failed_checks


def _review_followups(states, history, now_ts, quiz_reviews=()):
    """Deriva las tareas pendientes y los temas que requieren evidencia directa."""
    failures, last_pass, failed_checks = history
    checks = {}
    retries = {}
    protected = set()
    for topic_id, (count, trigger) in failures.items():
        state = states.get(topic_id, {})
        if state.get("mastery", 0.0) < 0.75:
            continue
        protected.add(topic_id)
        due = compute_retention(state, now_ts)["due_for_review"]
        if count < RECOVERY_FAILURES:
            if due:
                retries[topic_id] = ("review", "El último repaso quedó bajo el 65 %. Resuelve otra variante para comprobar la retención.")
            continue

        topic = TOPICS_BY_ID[topic_id]
        needs_check = False
        for prerequisite_id in topic["prereqs"]:
            failed_check = failed_checks.get(prerequisite_id, -1)
            if last_pass.get(prerequisite_id, -1) > max(trigger, failed_check):
                continue
            prerequisite = states.get(prerequisite_id, {})
            if failed_check > trigger:
                task = ("recovery", f"La comprobación directa para «{topic['title']}» quedó bajo el 65 %. Practica el prerrequisito con un ejemplo resuelto.")
            elif prerequisite.get("mastery", 0.0) < 0.70:
                task = ("prerequisite_check", f"Prerrequisito de «{topic['title']}», con repasos fallidos consecutivos. Su maestría estimada está bajo el 70 %.")
            elif compute_retention(prerequisite, now_ts)["due_for_review"]:
                task = ("prerequisite_check", f"Prerrequisito de «{topic['title']}», con repasos fallidos consecutivos. Su repaso está vencido.")
            else:
                continue
            needs_check = True
            protected.add(prerequisite_id)
            checks.setdefault(prerequisite_id, task)

        if due and not needs_check:
            retries[topic_id] = ("recovery", f"Hay {count} repasos fallidos consecutivos. Revisa el ejemplo y practica con otras variantes.")
    for topic_id, task in retries.items():
        checks.setdefault(topic_id, task)
    quiz_tasks = {
        topic_id: ("quiz_review", "Fallaste una pregunta de este tema en el quiz. Comprueba la habilidad con otras variantes.")
        for topic_id in quiz_reviews
    }
    for topic_id in quiz_tasks:
        checks.pop(topic_id, None)
    return {**quiz_tasks, **checks}, protected | quiz_tasks.keys()


def get_full_state():
    """Devuelve el estado completo del estudiante, grafo de tópicos y cola de estudio adaptativa."""
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    if isinstance(conn, sqlite3.Connection):
        cur.execute("BEGIN")

    diagnostic_row = _diagnostic_row(cur)
    study_row = _study_row(cur)
    progress = json.loads(study_row["data_json"])
    profile_row = dict(cur.execute("SELECT * FROM user_profile WHERE id = 1").fetchone())
    profile = dict(profile_row)
    raw_states = {
        r["topic_id"]: dict(r)
        for r in cur.execute("SELECT * FROM topic_state").fetchall()
    }
    xp_logs = [dict(r) for r in cur.execute("SELECT * FROM xp_log ORDER BY id ASC").fetchall()]
    conn.close()

    today = datetime.date.today()
    week = {
        day: {"date": day, "xp": 0, "sessions": 0}
        for day in ((today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1))
    }
    for entry in xp_logs:
        day = week.get(entry["date_str"])
        if day is not None:
            day["xp"] += entry["xp_earned"]
            day["sessions"] += 1
    profile["today_xp"] = week[today.isoformat()]["xp"]
    now_ts = datetime.datetime.now().timestamp()
    enriched_topics = []

    for t in TOPICS:
        tid = t["id"]
        st = raw_states.get(tid, {})
        ret_info = compute_retention(st, now_ts)
        mastery = float(st.get("mastery", 0.0))

        prereqs = t["prereqs"]
        met_prereqs = [p for p in prereqs if float(raw_states.get(p, {}).get("mastery", 0.0)) >= 0.70]

        if mastery >= 0.75:
            status = "review_due" if ret_info["due_for_review"] else "mastered"
        elif len(met_prereqs) == len(prereqs):
            status = "in_progress" if mastery > 0.0 else "available"
        else:
            status = "locked"

        # Cuántos temas futuros desbloquea este nodo (valor estratégico en el DAG)
        unlocks = [
            other["id"] for other in TOPICS if tid in other["prereqs"]
        ]
        course = COURSES_BY_ID[t["course_id"]]
        enriched_topics.append(
            {
                "id": tid,
                "title": t["title"],
                "course_id": t["course_id"],
                "course_name": course["name"],
                "course_code": course["code"],
                "semester": t["semester"],
                "domain": t["domain"],
                "xp": t["xp"],
                "estimated_mins": t["estimated_mins"],
                "prereqs": prereqs,
                "met_prereqs": met_prereqs,
                "unlocks": unlocks,
                "status": status,
                "mastery": round(mastery, 2),
                "retention": ret_info["retention"],
                "days_elapsed": ret_info["days_elapsed"],
                "stability_days": round(float(st.get("stability_days", 2.0)), 1),
                "repetitions": int(st.get("repetitions", 0)),
                "due_for_review": ret_info["due_for_review"],
            }
        )

    # Construir la Cola de Tareas Adaptativas (Math Academy Task Queue)
    followups, protected = _review_followups(raw_states, _review_history(xp_logs), now_ts, progress["quiz_reviews"])
    recommendations = build_recommendations(
        enriched_topics, profile["current_semester"], followups, protected
    )

    # Estadísticas por curso
    course_summaries = []
    for c in COURSES:
        c_topics = [t for t in enriched_topics if t["course_id"] == c["id"]]
        mastered_cnt = sum(1 for t in c_topics if t["status"] in ("mastered", "review_due"))
        avg_mastery = (
            sum(t["mastery"] for t in c_topics) / len(c_topics) if c_topics else 0.0
        )
        course_summaries.append(
            {
                **c,
                "total_topics": len(c_topics),
                "mastered_topics": mastered_cnt,
                "progress_pct": round(avg_mastery * 100),
            }
        )

    backend_name = get_storage_backend_name()
    return {
        "storage_backend": backend_name,
        "profile": profile,
        "diagnostic": diagnostic.public_session(_read_diagnostic_session(diagnostic_row))["status"],
        "preset_mode": diagnostic_row["preset_mode"],
        "courses": course_summaries,
        "topics": enriched_topics,
        "recommendations": recommendations,
        "activity_7d": list(week.values()),
        "study": _study_overview(progress, raw_states, _read_diagnostic_session(diagnostic_row)),
        "backup_snapshot": {
            "version": 1,
            "exported_at": datetime.datetime.now().isoformat(),
            "updated_at_ts": now_ts,
            "storage_backend": backend_name,
            "profile": profile_row,
            "topic_state": list(raw_states.values()),
            "xp_log": xp_logs,
            "diagnostic": _diagnostic_backup(diagnostic_row),
            "study": {"revision": study_row["revision"], "progress": progress},
        },
    }


def build_recommendations(enriched_topics, current_semester, followups=None, protected=()):
    """
    Selecciona hasta 4 tareas óptimas combinando:
    1. Repasos que ya vencieron y comprobaciones directas pendientes.
    2. Lecciones de la frontera del semestre actual (Semestre 1-2).
    3. Lecciones de anticipación estratégica (Semestres siguientes desbloqueados).
    """
    by_id = {t["id"]: t for t in enriched_topics}
    followups = followups or {}
    tasks = []

    candidates = [
        t
        for t in enriched_topics
        if t["id"] not in protected and t["status"] in ("available", "in_progress", "review_due")
    ]

    def score_candidate(t):
        sem_diff = t["semester"] - current_semester
        if sem_diff == 0:
            sem_bonus = 3.0
        elif sem_diff < 0:
            sem_bonus = 3.5
        elif sem_diff == 1:
            sem_bonus = 2.2  # Anticipación inmediata
        else:
            sem_bonus = 1.2  # Anticipación avanzada

        status_bonus = {
            "review_due": 3.2,
            "in_progress": 2.8,
            "available": 2.5,
        }.get(t["status"], 0.0)

        # Si el estudiante acaba de intentar este nodo hace menos de ~30 min y quedó en progreso,
        # rotamos la cola para no bloquear la primera tarjeta con el mismo tema inmediatamente.
        recency_penalty = (
            -1.5
            if (
                t["status"] == "in_progress"
                and t.get("repetitions", 0) > 0
                and t.get("days_elapsed", 99.0) < 0.02
            )
            else 0.0
        )

        unlock_bonus = 0.35 * len(t["unlocks"])
        return status_bonus + sem_bonus + unlock_bonus + recency_penalty

    ranked = [by_id[tid] for tid in followups]
    ranked.extend(sorted(
        (t for t in candidates if t["id"] not in followups),
        key=lambda t: (t["status"] == "review_due", score_candidate(t)),
        reverse=True,
    ))

    for t in ranked:
        tid = t["id"]
        if tid in followups:
            task_type, reason = followups[tid]
            tag_label = {
                "review": "Repaso directo",
                "recovery": "Recuperación guiada",
                "prerequisite_check": "Comprobación de prerrequisito",
                "quiz_review": "Repaso del quiz",
            }[task_type]
        elif t["status"] == "review_due":
            task_type = "review"
            tag_label = "Repaso espaciado"
            reason = f"Venció el intervalo de repaso. Retención estimada: {t['retention']:.0%}."
        elif t["semester"] > current_semester:
            task_type = "anticipation"
            tag_label = f"Anticipación Semestre {t['semester']}"
            reason = "Sus prerrequisitos permiten adelantar un tema de un semestre posterior."
        elif t["status"] == "in_progress":
            task_type = "lesson"
            tag_label = f"En Progreso · Semestre {t['semester']}"
            reason = "Ya practicaste el tema y puedes seguir avanzando."
        else:
            task_type = "lesson"
            tag_label = f"Frontera Semestre {t['semester']}"
            reason = "El tema está disponible según sus prerrequisitos."

        tasks.append(
            {
                "topic_id": t["id"],
                "title": t["title"],
                "course_id": t["course_id"],
                "course_name": t["course_name"],
                "semester": t["semester"],
                "domain": t["domain"],
                "task_type": task_type,
                "tag_label": tag_label,
                "reason": reason,
                "xp": t["xp"] if task_type != "review" else max(6, int(t["xp"] * 0.7)),
                "estimated_mins": t["estimated_mins"],
                "mastery": t["mastery"],
                "retention": t["retention"],
                "unlocks_count": len(t["unlocks"]),
            }
        )
        if len(tasks) >= 4:
            break

    # Si todos los temas están dominados y ninguno vence hoy, ofrecer práctica de refuerzo/velocidad
    if not tasks:
        for t in [topic for topic in enriched_topics if topic["id"] not in protected][:3]:
            tasks.append(
                {
                    "topic_id": t["id"],
                    "title": t["title"],
                    "course_id": t["course_id"],
                    "course_name": t["course_name"],
                    "semester": t["semester"],
                    "domain": t["domain"],
                    "task_type": "practice",
                    "tag_label": "Entrenamiento de Velocidad",
                    "reason": "Puedes practicar mientras llega el próximo repaso.",
                    "xp": 8,
                    "estimated_mins": 6,
                    "mastery": t["mastery"],
                    "retention": t["retention"],
                    "unlocks_count": len(t["unlocks"]),
                }
            )

    return tasks


def _shuffle_question_options(q, is_parametric=False, *, rng=random):
    """Copia una pregunta y baraja sus alternativas actualizando correct_index."""
    q_copy = dict(q, is_parametric=is_parametric)
    opts = list(q_copy.get("options", []))
    corr_idx = int(q_copy.get("correct_index", 0))
    if 0 <= corr_idx < len(opts):
        correct_opt = opts[corr_idx]
        rng.shuffle(opts)
        q_copy["options"] = opts
        q_copy["correct_index"] = opts.index(correct_opt)
    return q_copy


def get_topic_lesson_payload(topic_id, *, seed=None, task_type="lesson"):
    """Devuelve la lección completa con preguntas curadas + preguntas paramétricas generadas al vuelo."""
    t = TOPICS_BY_ID.get(topic_id)
    if not t:
        return None
    course = COURSES_BY_ID[t["course_id"]]
    seed_info = {}
    rng = random
    if t["course_id"] == "IC":
        seed = random.getrandbits(32) if seed is None else seed
        rng = random.Random(seed)
        seed_info["exercise_seed"] = seed
    generated_only = t["course_id"] == "IC" and task_type in DIRECT_RETRIEVAL_TASKS
    count = 3 if generated_only else 2
    if t["generator_type"] == "continuity_param" and task_type == "review":
        dynamic_qs = generate_parametric_questions(t["generator_type"], count=2, rng=rng)
        dynamic_qs.append(gen_continuous_radical_extension(rng=rng))
        rng.shuffle(dynamic_qs)
    else:
        dynamic_qs = generate_parametric_questions(t["generator_type"], count=count, rng=rng)
        while generated_only and len({q["prompt"] for q in dynamic_qs}) < count:
            dynamic_qs = generate_parametric_questions(t["generator_type"], count=count, rng=rng)
    all_questions = dynamic_qs
    if not generated_only:
        all_questions = [_shuffle_question_options(q, rng=rng) for q in t["questions"]] + dynamic_qs

    return {
        **seed_info,
        "id": t["id"],
        "title": t["title"],
        "course_id": t["course_id"],
        "course_name": course["name"],
        "course_code": course["code"],
        "semester": t["semester"],
        "domain": t["domain"],
        "xp": t["xp"],
        "estimated_mins": t["estimated_mins"],
        "prereqs": [
            {"id": p, "title": TOPICS_BY_ID[p]["title"]} for p in t["prereqs"]
        ],
        "theory": t["theory"],
        "ds_connection": t["ds_connection"],
        "uc_exam_tip": t["uc_exam_tip"],
        "worked_example": t["worked_example"],
        "questions": all_questions,
    }


def record_completion(topic_id, correct_count, total_count, task_type="lesson"):
    """
    Registra un resultado agregado. Un fallo acorta el repaso de un tópico ya aprendido.
    """
    init_db()
    conn = get_conn()
    try:
        cur = conn.cursor()
        progress = json.loads(_lock_study_row(conn, cur)["data_json"])
        result, writes = _completion_writes(
            cur, topic_id, correct_count, total_count, task_type, datetime.datetime.now(), progress
        )
        _commit_writes(conn, cur, writes)
        return result
    finally:
        conn.close()


def _completion_writes(cur, topic_id, correct_count, total_count, task_type, now, progress, *, evidence=None):
    if topic_id not in TOPICS_BY_ID:
        raise ValueError("Tópico no encontrado")

    topic = TOPICS_BY_ID[topic_id]
    total_count = max(1, int(total_count))
    correct_count = max(0, min(total_count, int(correct_count)))
    score_ratio = correct_count / total_count
    passed = score_ratio >= PASS_SCORE

    now_ts = now.timestamp()
    writes = []

    st = dict(
        cur.execute(
            "SELECT * FROM topic_state WHERE topic_id = ?", (topic_id,)
        ).fetchone()
    )
    old_mastery = float(st["mastery"])
    old_stability = min(90.0, float(st["stability_days"]))
    reps = int(st["repetitions"])
    was_mastered = old_mastery >= 0.75
    review_scheduled = passed or was_mastered
    mastery_evidence = None
    new_mastery = old_mastery
    new_stability = float(st["stability_days"])
    recovery_scheduled = False

    history = _review_history(cur.execute(
        "SELECT topic_id, task_type, score_ratio FROM xp_log ORDER BY id ASC"
    ).fetchall())

    if passed:
        mastery_evidence = 0.75 + 0.25 * score_ratio
        new_mastery = max(old_mastery, mastery_evidence)
        growth_factor = 1.8 + 0.9 * score_ratio
        new_stability = 4.0
        if reps > 0 or was_mastered:
            new_stability = min(90.0, max(1.5, old_stability) * growth_factor)
    elif was_mastered:
        new_stability = max(1.0, round(old_stability * 0.55, 1))
        failures, _, _ = history
        failure_count, _ = failures.get(topic_id, (0, -1))
        if task_type in ("review", "recovery"):
            recovery_scheduled = failure_count + (task_type == "review") >= RECOVERY_FAILURES
        if recovery_scheduled:
            new_stability = RECOVERY_INTERVAL_DAYS

    if review_scheduled:
        writes.append((
            """
            UPDATE topic_state
            SET mastery = CASE WHEN mastery < ? THEN ? ELSE mastery END,
                stability_days = ?,
                repetitions = repetitions + 1,
                last_practiced_ts = ?,
                next_review_ts = ?,
                total_attempts = total_attempts + ?,
                correct_attempts = correct_attempts + ?
            WHERE topic_id = ?
            """,
            (
                mastery_evidence,
                mastery_evidence,
                new_stability,
                now_ts,
                now_ts + new_stability * 86400.0,
                total_count,
                correct_count,
                topic_id,
            ),
        ))
    else:
        writes.append((
            """
            UPDATE topic_state
            SET total_attempts = total_attempts + ?,
                correct_attempts = correct_attempts + ?
            WHERE topic_id = ?
            """,
            (total_count, correct_count, topic_id),
        ))

    implicit_boosted = []
    if passed and evidence:
        states = {
            row["topic_id"]: dict(row)
            for row in cur.execute("SELECT * FROM topic_state").fetchall()
        }
        _, protected = _review_followups(states, history, now_ts, progress["quiz_reviews"])
        for sub_id, observations in evidence.items():
            sub_row = states.get(sub_id)
            if not sub_row or sub_id in protected:
                continue
            dose = sum(item["weight"] for item in observations) / total_count
            schedule = fire.extended_schedule(sub_row, dose, now_ts)
            if schedule is None:
                continue
            stability, next_review, postponed = schedule
            writes.append((
                "UPDATE topic_state SET stability_days = ?, next_review_ts = ? WHERE topic_id = ?",
                (stability, next_review, sub_id),
            ))
            implicit_boosted.append({
                "id": sub_id,
                "title": TOPICS_BY_ID[sub_id]["title"],
                "weight": dose,
                "new_stability_days": round(stability, 1),
                "postponed_days": round(postponed, 2),
                "next_review_ts": next_review,
                "evidence": observations,
            })

    # Cálculo de XP (Math Academy otorga XP completo al aprobar y bono por perfección)
    base_xp = int(topic["xp"])
    if passed:
        xp_earned = base_xp + (3 if score_ratio == 1.0 else 0)
    else:
        xp_earned = max(3, int(round(base_xp * max(0.3, 0.5 * score_ratio))))

    writes.extend(_activity_writes(cur, topic_id, task_type, xp_earned, score_ratio, now, implicit_boosted))
    return {
        "passed": passed,
        "score_ratio": score_ratio,
        "xp_earned": xp_earned,
        "new_mastery": round(new_mastery, 2),
        "new_stability_days": round(new_stability, 1),
        "review_scheduled": review_scheduled,
        "recovery_scheduled": recovery_scheduled,
        "implicit_boosted": implicit_boosted,
    }, writes


def _activity_writes(cur, topic_id, task_type, xp_earned, score_ratio, now, implicit_boosted=()):
    today_str = now.date().isoformat()
    yesterday_str = (now.date() - datetime.timedelta(days=1)).isoformat()
    log = (
        """
        INSERT INTO xp_log (date_str, topic_id, task_type, xp_earned, score_ratio, implicit_topics_json, created_ts)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            today_str,
            topic_id,
            task_type,
            xp_earned,
            score_ratio,
            json.dumps(implicit_boosted, ensure_ascii=False),
            now.timestamp(),
        ),
    )

    prof_row = cur.execute("SELECT streak_days, last_active_date FROM user_profile WHERE id = 1").fetchone()
    old_streak = int(prof_row["streak_days"]) if prof_row else 1
    last_date = prof_row["last_active_date"] if prof_row else None
    if last_date == today_str:
        new_streak = old_streak
    elif last_date == yesterday_str:
        new_streak = old_streak + 1
    else:
        new_streak = max(1, old_streak)

    update_profile = (
        """
        UPDATE user_profile
        SET total_xp = total_xp + ?, streak_days = ?, last_active_date = ?
        WHERE id = 1
        """,
        (xp_earned, new_streak, today_str),
    )

    return [log, update_profile]


def _study_row(cur, *, lock=False):
    sql = "SELECT * FROM study_state WHERE id = 1"
    return dict(cur.execute(sql + (" FOR UPDATE" if lock else "")).fetchone())


def _lock_study_row(conn, cur):
    if isinstance(conn, sqlite3.Connection):
        cur.execute("BEGIN IMMEDIATE")
    return _study_row(cur, lock=isinstance(conn, _PostgresConnWrapper))


def _commit_writes(conn, cur, writes):
    if isinstance(conn, _TursoConn):
        cur.write_batch(writes)
    else:
        for sql, params in writes:
            cur.execute(sql, params)
        conn.commit()


def _study_overview(progress, states, diagnostic_session):
    lessons = [
        study.lesson_overview(lesson, slot)
        for slot, lesson in progress["lessons"].items() if lesson["result"] is None
    ]
    last_slot = progress["last_lesson"]
    last = study.lesson_overview(progress["lessons"][last_slot], last_slot) if last_slot else None
    eligible = study.eligible_topics(states, progress, diagnostic_session)
    return {
        "lessons": lessons,
        "last_lesson": last,
        "quiz": study.quiz_overview(progress["quiz"], len(eligible)),
        "quiz_reviews": list(progress["quiz_reviews"]),
    }


def _new_study_lesson(progress, topic_id, task_type):
    if topic_id not in diagnostic.PILOT_TOPIC_IDS:
        return study.new_lesson(get_topic_lesson_payload(topic_id, task_type=task_type), task_type)
    quiz = progress["quiz"]
    excluded = {progress["quiz_reviews"].get(topic_id)}
    if study.quiz_overview(quiz, 0)["status"] == "in_progress":
        excluded.update(
            study.prompt_key(study.quiz_question(variant)["prompt"])
            for variant in quiz["variants"] if variant["topic_id"] == topic_id
        )
    for _ in range(128):
        topic = get_topic_lesson_payload(topic_id, task_type=task_type)
        keys = {study.prompt_key(question["prompt"]) for question in topic["questions"]}
        if not keys & excluded:
            progress["seen"] = sorted(set(progress["seen"]) | keys)
            lesson = study.new_lesson(topic, task_type)
            if task_type == "quiz_review":
                lesson["quiz_error"] = progress["quiz_reviews"].get(topic_id)
            return lesson
    raise ValueError("No se encontró una variante de práctica disponible. Intenta otra vez.")


def _lesson_transition(cur, progress, body, now):
    action = body.get("action")
    if action == "open":
        topic_id = body.get("topic_id")
        task_type = body.get("task_type", "lesson")
        if topic_id not in TOPICS_BY_ID or task_type not in study.LESSON_TASKS:
            raise ValueError("Tema o tipo de práctica desconocido.")
        slot = f"{topic_id}:{task_type}"
        lesson = progress["lessons"].get(slot)
        if lesson is None or lesson["result"] is not None:
            lesson = _new_study_lesson(progress, topic_id, task_type)
            progress["lessons"][slot] = lesson
            if progress["last_lesson"] == slot:
                progress["last_lesson"] = None
        return {**lesson, "slot": slot}, []

    slot = body.get("slot")
    lesson = progress["lessons"].get(slot)
    if lesson is None or lesson["id"] != body.get("session_id"):
        raise ValueError("La sesión cambió. Vuelve a abrirla desde el panel.")
    writes = []
    if action in ("advance", "hint") and study.advance_lesson(progress, lesson, body, now.timestamp()):
        topic = lesson["topic"]
        topic_id = topic["id"]
        task_type = lesson["task_type"]
        questions = topic["questions"]
        answers = lesson["answers"]
        total = len(questions)
        correct = sum(choice == q["correct_index"] for choice, q in zip(answers, questions, strict=True))
        evidence = None
        if task_type == "review" and correct / total >= PASS_SCORE and os.environ.get("FIRE_ENABLED") != "0":
            evidence = fire.review_evidence(topic_id, questions, answers)
        lesson["result"], writes = _completion_writes(
            cur, topic_id, correct, total, task_type, now, progress, evidence=evidence
        )
        lesson["step"] = total + 1
        progress["last_lesson"] = slot
        if (task_type == "quiz_review" and lesson["result"]["passed"]
                and progress["quiz_reviews"].get(topic_id) == lesson.get("quiz_error")):
            progress["quiz_reviews"].pop(topic_id, None)
    return {**lesson, "slot": slot}, writes


def _quiz_transition(cur, progress, body, now):
    states = {row["topic_id"]: dict(row) for row in cur.execute("SELECT * FROM topic_state").fetchall()}
    diagnostic_session = _read_diagnostic_session(_diagnostic_row(cur))
    eligible = study.eligible_topics(states, progress, diagnostic_session)
    quiz = progress["quiz"]
    overview = study.quiz_overview(quiz, len(eligible))
    action = body.get("action")
    writes = []
    if action == "open" and (quiz is None or (
        overview["status"] == "completed" and body.get("restart_from") == quiz["id"]
    )):
        seen = set(progress["seen"]) | study.diagnostic_keys(diagnostic_session)
        quiz = study.new_quiz(eligible, seen, random.getrandbits(32))
        progress["quiz"] = quiz
        progress["seen"] = sorted(seen)
    elif quiz is None:
        raise ValueError("El quiz cambió. Vuelve a abrirlo desde el panel.")
    elif action == "advance" and (
        overview["status"] == "in_progress" and body.get("session_id") == quiz["id"]
        and body.get("answered") == overview["answered"]
    ):
        variant = quiz["variants"][overview["answered"]]
        study.confirm_answer(
            progress, quiz, study.quiz_question(variant), body.get("choice"), now.timestamp(),
            topic_id=variant["topic_id"], task_type="quiz", hint_used=False,
        )
        if len(quiz["answers"]) == overview["total"]:
            results = study.quiz_results(quiz)
            errors = {
                item["topic_id"]: study.prompt_key(item["prompt"]) for item in results if not item["correct"]
            }
            progress["quiz_reviews"].update(errors)
            correct = len(results) - len(errors)
            writes = _activity_writes(cur, "IC", "quiz", correct, correct / len(results), now)
    return study.public_quiz(quiz, len(eligible)), writes


def advance_study(body):
    """Guarda cada paso. El cierre y los XP se confirman en la misma transacción."""
    kind = body.get("kind")
    action = body.get("action")
    if kind not in ("lesson", "quiz") or (
        action not in ("open", "resume", "advance") and (kind, action) != ("lesson", "hint")
    ):
        raise ValueError("Acción de estudio desconocida.")
    init_db()
    conn = get_conn()
    try:
        cur = conn.cursor()
        row = _lock_study_row(conn, cur)
        progress = json.loads(row["data_json"])
        now = datetime.datetime.now()
        transition = _lesson_transition if kind == "lesson" else _quiz_transition
        session, writes = transition(cur, progress, body, now)
        encoded = json.dumps(progress, ensure_ascii=False)
        if encoded != row["data_json"] or writes:
            revision = max(now.timestamp(), row["revision"] + 0.001)
            # Un conflicto remoto aborta el lote completo mediante la restricción NOT NULL.
            _commit_writes(conn, cur, [(
                """UPDATE study_state
                   SET data_json = CASE WHEN revision = ? THEN ? ELSE NULL END, revision = ?
                   WHERE id = 1""",
                (row["revision"], encoded, revision),
            ), *writes])
        return session
    finally:
        conn.close()


def _diagnostic_row(cur):
    return dict(cur.execute("SELECT * FROM diagnostic_state WHERE id = 1").fetchone())


def _read_diagnostic_session(row):
    return json.loads(row["session_json"]) if row["session_json"] is not None else None


def _diagnostic_backup(row):
    return {
        "session": diagnostic.backup_session(_read_diagnostic_session(row)),
        "preset_mode": row["preset_mode"],
        "revision": row["revision"],
    }


def _next_diagnostic_revision(row, now_ts):
    return max(now_ts, row["revision"] + 0.001)


def _diagnostic_result_writes(session, encoded):
    writes = [(
        """UPDATE user_profile SET diagnostic_completed = 1 WHERE id = 1
           AND EXISTS (SELECT 1 FROM diagnostic_state WHERE id = 1 AND session_json = ?)""",
        (encoded,),
    )]
    for item in diagnostic.evidence(session["answers"]):
        if not item["correct"] or item["incorrect"]:
            continue
        tid = item["topic_id"]
        observed_at = max(a["answered_at"] for a in session["answers"] if a["topic_id"] == tid)
        days = diagnostic.INITIAL_REVIEW_DAYS
        writes.append((
            """
            UPDATE topic_state
            SET mastery = ?,
                stability_days = CASE WHEN next_review_ts IS NULL THEN ? ELSE stability_days END,
                repetitions = MAX(repetitions, 1),
                last_practiced_ts = CASE WHEN next_review_ts IS NULL THEN ? ELSE last_practiced_ts END,
                next_review_ts = COALESCE(next_review_ts, ?)
            WHERE topic_id = ? AND mastery < ?
              AND EXISTS (SELECT 1 FROM diagnostic_state WHERE id = 1 AND session_json = ?)
            """,
            (diagnostic.INITIAL_MASTERY, days, observed_at, observed_at + days * 86400,
             tid, diagnostic.INITIAL_MASTERY, encoded),
        ))
    return writes


def get_diagnostic_session():
    init_db()
    conn = get_conn()
    try:
        return diagnostic.public_session(_read_diagnostic_session(_diagnostic_row(conn.cursor())))
    finally:
        conn.close()


def advance_diagnostic(body):
    """Aplica una transición identificada por la sesión y el número de pregunta."""
    init_db()
    conn = get_conn()
    try:
        cur = conn.cursor()
        row = _diagnostic_row(cur)
        session = _read_diagnostic_session(row)
        now_ts = datetime.datetime.now().timestamp()
        if body.get("start") is True:
            restart = (
                session is not None and session["current"] is None
                and body.get("restart_from") == session["id"]
            )
            if session is not None and not restart:
                return diagnostic.public_session(session)
            seed = random.getrandbits(32)
            session = {
                "id": uuid.uuid4().hex, "seed": seed, "answers": [],
                "current": diagnostic.next_question(seed, []),
                "previous_prompts": sorted(study.diagnostic_keys(session)),
            }
        else:
            if "choice" not in body or type(body.get("answered")) is not int or not body.get("session_id"):
                raise ValueError("Identifica la pregunta y envía una alternativa o una omisión.")
            if (session is None or session["current"] is None
                    or body["session_id"] != session["id"] or body["answered"] != len(session["answers"])):
                return diagnostic.public_session(session)
            session = diagnostic.record_answer(session, body["choice"], now_ts)

        encoded = json.dumps(session, ensure_ascii=False)
        writes = [(
            "UPDATE diagnostic_state SET session_json = ?, revision = ? WHERE id = 1 AND revision = ?",
            (encoded, _next_diagnostic_revision(row, now_ts), row["revision"]),
        )]
        if session["current"] is None:
            writes.extend(_diagnostic_result_writes(session, encoded))
        if isinstance(conn, _TursoConn):
            cur.write_batch(writes)
        else:
            for sql, params in writes:
                cur.execute(sql, params)
            conn.commit()
        return diagnostic.public_session(_read_diagnostic_session(_diagnostic_row(cur)))
    finally:
        conn.close()


def update_profile_settings(current_semester=None, daily_goal_xp=None, preset_mode=None):
    """Actualiza preferencias o aplica un preset rápido (ej. Mitad Semestre 1, Fin Semestre 1, Reset)."""
    init_db()
    now_ts = datetime.datetime.now().timestamp()
    conn = get_conn()
    cur = conn.cursor()

    if preset_mode == "reset":
        study_row = _lock_study_row(conn, cur)
        cur.execute(
            "UPDATE study_state SET data_json = ?, revision = ? WHERE id = 1",
            (json.dumps(study.empty_state()), max(now_ts, study_row["revision"] + 0.001)),
        )
    if preset_mode in ("reset", "mid_sem1", "sem2_ready"):
        row = _diagnostic_row(cur)
        cur.execute(
            "UPDATE diagnostic_state SET session_json = NULL, preset_mode = ?, revision = ? WHERE id = 1",
            (None if preset_mode == "reset" else preset_mode, _next_diagnostic_revision(row, now_ts)),
        )
    if current_semester is not None:
        cur.execute(
            "UPDATE user_profile SET current_semester = ? WHERE id = 1",
            (max(1, min(4, int(current_semester))),),
        )
    if daily_goal_xp is not None:
        cur.execute(
            "UPDATE user_profile SET daily_goal_xp = ? WHERE id = 1",
            (max(10, min(120, int(daily_goal_xp))),),
        )

    if preset_mode == "reset":
        cur.execute(
            "UPDATE topic_state SET mastery = 0.0, stability_days = 2.0, repetitions = 0, last_practiced_ts = NULL, next_review_ts = NULL, total_attempts = 0, correct_attempts = 0"
        )
        cur.execute("DELETE FROM xp_log")
        cur.execute(
            """UPDATE user_profile SET total_xp = 0, diagnostic_completed = 0,
               current_semester = 1, last_active_date = NULL, streak_days = 1 WHERE id = 1"""
        )
    elif preset_mode == "mid_sem1":
        # Estudiante en mitad del Semestre 1 UC (domina bases de IC e IAG, con 1 repaso pendiente para mostrar FIRe)
        cur.execute(
            "UPDATE topic_state SET mastery = 0.0, stability_days = 2.0, repetitions = 0, last_practiced_ts = NULL, next_review_ts = NULL"
        )
        base_mastered = [
            ("ic_desigualdades", 0.92, 4.0, now_ts - 5.0 * 86400.0),  # Vencido para repaso FIRe
            ("ic_funciones", 0.88, 6.0, now_ts - 1.5 * 86400.0),
            ("iag_logica_conjuntos", 0.94, 7.0, now_ts - 2.0 * 86400.0),
            ("iag_induccion_sumatorias", 0.86, 5.0, now_ts - 1.0 * 86400.0),
        ]
        for tid, m, s, lts in base_mastered:
            cur.execute(
                """
                UPDATE topic_state
                SET mastery = ?, stability_days = ?, repetitions = 2, last_practiced_ts = ?, next_review_ts = ?
                WHERE topic_id = ?
                """,
                (m, s, lts, lts + s * 86400.0, tid),
            )
        cur.execute(
            "UPDATE user_profile SET current_semester = 1, diagnostic_completed = 0, total_xp = MAX(total_xp, 45) WHERE id = 1"
        )
    elif preset_mode == "sem2_ready":
        # Estudiante que completó todo Semestre 1 y quiere anticipar Semestre 2 (Cálculo I + Álgebra Lineal CD)
        for t in TOPICS:
            if t["semester"] == 1:
                cur.execute(
                    """
                    UPDATE topic_state
                    SET mastery = 0.92, stability_days = 10.0, repetitions = 3, last_practiced_ts = ?, next_review_ts = ?
                    WHERE topic_id = ?
                    """,
                    (now_ts - 2.0 * 86400.0, now_ts + 8.0 * 86400.0, t["id"]),
                )
        cur.execute(
            "UPDATE user_profile SET current_semester = 2, diagnostic_completed = 0, total_xp = MAX(total_xp, 100) WHERE id = 1"
        )

    conn.commit()
    conn.close()
    return get_full_state()


def export_backup_payload():
    """Exporta todo el progreso (perfil, estado de nodos y registro XP) en un JSON portable."""
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    if isinstance(conn, sqlite3.Connection):
        cur.execute("BEGIN")
    diagnostic_backup = _diagnostic_backup(_diagnostic_row(cur))
    study_row = _study_row(cur)
    profile = dict(cur.execute("SELECT * FROM user_profile WHERE id = 1").fetchone())
    topic_states = [dict(r) for r in cur.execute("SELECT * FROM topic_state").fetchall()]
    xp_logs = [dict(r) for r in cur.execute("SELECT * FROM xp_log ORDER BY id ASC").fetchall()]
    conn.close()
    return {
        "version": 1,
        "exported_at": datetime.datetime.now().isoformat(),
        "storage_backend": get_storage_backend_name(),
        "profile": profile,
        "topic_state": topic_states,
        "xp_log": xp_logs,
        "diagnostic": diagnostic_backup,
        "study": {"revision": study_row["revision"], "progress": json.loads(study_row["data_json"])},
    }


def import_backup_payload(payload, *, expected_revisions=None):
    """Restaura un respaldo JSON en la base de datos activa (Cloud o Local)."""
    diagnostic_backup = payload.get("diagnostic") or {}
    session = diagnostic.restore_session(diagnostic_backup.get("session"))
    encoded = json.dumps(session, ensure_ascii=False) if session is not None else None
    preset_mode = diagnostic_backup.get("preset_mode")
    revision = float(diagnostic_backup.get("revision", 0))
    study_backup = payload.get("study") or {}
    study_revision = float(study_backup.get("revision", 0))
    progress = study_backup.get("progress", study.empty_state())
    if not isinstance(progress, dict):
        raise ValueError("El respaldo de las sesiones de estudio no es válido.")
    progress = {"first_attempts": [], **progress}
    if progress.keys() != study.empty_state().keys() or not isinstance(progress["first_attempts"], list):
        raise ValueError("El respaldo de las sesiones de estudio no es válido.")
    init_db()
    conn = get_conn()
    try:
        cur = conn.cursor()
        saved_study = _lock_study_row(conn, cur)
        saved_diagnostic = _diagnostic_row(cur)
        if expected_revisions is not None:
            if expected_revisions != (saved_diagnostic["revision"], saved_study["revision"]):
                return None
        elif saved_study["revision"] > 0:
            study_revision = max(study_revision, saved_study["revision"] + 0.001)
        cur.execute(
            "UPDATE study_state SET data_json = ?, revision = ? WHERE id = 1",
            (json.dumps(progress, ensure_ascii=False), study_revision),
        )
        cur.execute(
            "UPDATE diagnostic_state SET session_json = ?, preset_mode = ?, revision = ? WHERE id = 1",
            (encoded, preset_mode, revision),
        )
        _restore_backup_rows(cur, payload)
        conn.commit()
    finally:
        conn.close()
    return get_full_state()


def _restore_backup_rows(cur, payload):
    prof = payload.get("profile") or {}
    if prof:
        cur.execute(
            """
            UPDATE user_profile
            SET name = ?,
                current_semester = ?,
                daily_goal_xp = ?,
                total_xp = ?,
                streak_days = ?,
                last_active_date = ?,
                diagnostic_completed = ?
            WHERE id = 1
            """,
            (
                prof.get("name", "Estudiante Lic. Ingeniería en Ciencia de Datos UC"),
                int(prof.get("current_semester", 1)),
                int(prof.get("daily_goal_xp", 35)),
                int(prof.get("total_xp", 0)),
                int(prof.get("streak_days", 1)),
                prof.get("last_active_date"),
                int(prof.get("diagnostic_completed", 0)),
            ),
        )

    for st in payload.get("topic_state", []):
        tid = st.get("topic_id")
        if tid in TOPICS_BY_ID:
            cur.execute(
                """
                UPDATE topic_state
                SET mastery = ?,
                    stability_days = ?,
                    repetitions = ?,
                    last_practiced_ts = ?,
                    next_review_ts = ?,
                    total_attempts = ?,
                    correct_attempts = ?
                WHERE topic_id = ?
                """,
                (
                    float(st.get("mastery", 0.0)),
                    float(st.get("stability_days", 2.0)),
                    int(st.get("repetitions", 0)),
                    st.get("last_practiced_ts"),
                    st.get("next_review_ts"),
                    int(st.get("total_attempts", 0)),
                    int(st.get("correct_attempts", 0)),
                    tid,
                ),
            )

    if "xp_log" in payload and isinstance(payload["xp_log"], list):
        cur.execute("DELETE FROM xp_log")
        for row in payload["xp_log"]:
            cur.execute(
                """
                INSERT INTO xp_log (date_str, topic_id, task_type, xp_earned, score_ratio, implicit_topics_json, created_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("date_str", datetime.date.today().isoformat()),
                    row.get("topic_id", "unknown"),
                    row.get("task_type", "lesson"),
                    int(row.get("xp_earned", 0)),
                    float(row.get("score_ratio", 1.0)),
                    row.get("implicit_topics_json", "[]"),
                    float(row.get("created_ts", datetime.datetime.now().timestamp())),
                ),
            )

def ensure_hydrated_from_client(client_backup):
    """
    Sincroniza el estado enviado por el navegador (`client_backup`) con la base SQLite
    cuando se ejecuta en entorno serverless efímero (/tmp en Vercel) o cuando la base
    local está vacía/desactualizada respecto al respaldo del cliente.
    """
    if not isinstance(client_backup, dict):
        return False
    if "profile" not in client_backup or "topic_state" not in client_backup:
        return False
    if get_storage_backend_name() != "sqlite-local":
        return False

    init_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("BEGIN")
    srv_log_row = cur.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(MAX(created_ts), 0.0) AS max_ts FROM xp_log"
    ).fetchone()
    srv_cnt = int(srv_log_row["cnt"]) if srv_log_row else 0
    srv_max_ts = float(srv_log_row["max_ts"]) if srv_log_row else 0.0
    srv_revision = _diagnostic_row(cur)["revision"]
    srv_study_revision = _study_row(cur)["revision"]
    conn.close()

    cli_logs = (
        client_backup.get("xp_log")
        if isinstance(client_backup.get("xp_log"), list)
        else []
    )
    cli_cnt = len(cli_logs)
    cli_max_ts = max((float(r.get("created_ts", 0.0)) for r in cli_logs), default=0.0)
    cli_diagnostic = client_backup.get("diagnostic") or {}
    cli_revision = float(cli_diagnostic.get("revision", 0))
    cli_study_revision = float((client_backup.get("study") or {}).get("revision", 0))

    # Una copia anterior no puede hacer retroceder una pregunta ni deshacer el cierre.
    if cli_revision < srv_revision or cli_study_revision < srv_study_revision:
        return False
    if (cli_revision > srv_revision or cli_study_revision > srv_study_revision or cli_cnt > srv_cnt
            or cli_max_ts > srv_max_ts + 0.001 or (srv_cnt == 0 and srv_revision == 0 and srv_study_revision == 0)):
        return import_backup_payload(
            client_backup, expected_revisions=(srv_revision, srv_study_revision)
        ) is not None
    return False

