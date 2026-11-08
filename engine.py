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
import sqlite3

from curriculum import COURSES, TOPICS
from generators import generate_parametric_questions

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

    def execute(self, sql, params=()):
        stmt = {"sql": sql}
        if params:
            stmt["args"] = [self._convert_arg(p) for p in params]
        payload = json.dumps(
            {"requests": [{"type": "execute", "stmt": stmt}, {"type": "close"}]}
        ).encode("utf-8")
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
        exec_res = res0.get("response", {}).get("result", {})
        cols = [c["name"] for c in exec_res.get("cols", [])]
        self._rows = [
            {cols[i]: self._parse_cell(row[i]) for i in range(len(cols))}
            for row in exec_res.get("rows", [])
        ]
        return self

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
    cur.execute("SELECT COUNT(*) AS cnt FROM user_profile")
    if cur.fetchone()["cnt"] == 0:
        today = datetime.date.today().isoformat()
        cur.execute(
            """
            INSERT INTO user_profile (id, name, current_semester, daily_goal_xp, total_xp, streak_days, last_active_date, diagnostic_completed)
            VALUES (1, 'Estudiante Lic. Ingeniería en Ciencia de Datos UC', 1, 35, 0, 1, ?, 0)
            """,
            (today,),
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
    """Calcula la retención de memoria R(t) = exp(-Δt / S) y el estado del nodo."""
    if now_ts is None:
        now_ts = datetime.datetime.now().timestamp()
    mastery = float(row["mastery"])
    last_ts = row["last_practiced_ts"]
    stability = max(0.5, float(row["stability_days"]))
    reps = int(row["repetitions"])

    if reps == 0 or last_ts is None or mastery <= 0.05:
        return {
            "retention": 0.0,
            "days_elapsed": 0.0,
            "due_for_review": False,
        }

    days_elapsed = max(0.0, (now_ts - float(last_ts)) / 86400.0)
    retention = mastery * math.exp(-days_elapsed / stability)
    due = (row["next_review_ts"] is not None and now_ts >= float(row["next_review_ts"])) or (
        mastery >= 0.75 and retention < 0.78
    )
    return {
        "retention": round(min(1.0, max(0.0, retention)), 3),
        "days_elapsed": round(days_elapsed, 2),
        "due_for_review": bool(due),
    }


def get_Transitive_Encompassed(topic_id, min_weight=0.15):
    """
    Algoritmo FIRe: Calcula los pesos de repetición implícita fraccionaria
    hacia los prerrequisitos directos e indirectos en el DAG.
    """
    weights = {}
    queue = [(topic_id, 1.0)]
    while queue:
        curr_id, curr_w = queue.pop(0)
        topic = TOPICS_BY_ID.get(curr_id)
        if not topic:
            continue
        for sub_id, w in topic.get("encompasses", {}).items():
            new_w = round(curr_w * w, 3)
            if new_w >= min_weight and new_w > weights.get(sub_id, 0.0):
                weights[sub_id] = new_w
                queue.append((sub_id, new_w))
    return weights


def get_full_state():
    """Devuelve el estado completo del estudiante, grafo de tópicos y cola de estudio adaptativa."""
    init_db()
    conn = get_conn()
    cur = conn.cursor()

    profile = dict(cur.execute("SELECT * FROM user_profile WHERE id = 1").fetchone())
    today_str = datetime.date.today().isoformat()

    # XP ganado hoy
    row_today = cur.execute(
        "SELECT COALESCE(SUM(xp_earned), 0) AS today_xp FROM xp_log WHERE date_str = ?",
        (today_str,),
    ).fetchone()
    profile["today_xp"] = int(row_today["today_xp"])

    # Historial últimos 7 días
    seven_days = []
    for i in range(6, -1, -1):
        d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        r = cur.execute(
            "SELECT COALESCE(SUM(xp_earned), 0) AS xp, COUNT(*) AS sessions FROM xp_log WHERE date_str = ?",
            (d,),
        ).fetchone()
        seven_days.append({"date": d, "xp": int(r["xp"]), "sessions": int(r["sessions"])})

    raw_states = {
        r["topic_id"]: dict(r)
        for r in cur.execute("SELECT * FROM topic_state").fetchall()
    }
    conn.close()

    now_ts = datetime.datetime.now().timestamp()
    enriched_topics = []
    status_by_id = {}

    for t in TOPICS:
        tid = t["id"]
        st = raw_states.get(tid, {})
        ret_info = compute_retention(st, now_ts)
        mastery = float(st.get("mastery", 0.0))

        prereqs = t["prereqs"]
        prereqs_met = all(
            float(raw_states.get(p, {}).get("mastery", 0.0)) >= 0.70 for p in prereqs
        )

        if mastery >= 0.75:
            status = "review_due" if ret_info["due_for_review"] else "mastered"
        elif prereqs_met:
            status = "in_progress" if mastery > 0.0 else "available"
        else:
            status = "locked"

        status_by_id[tid] = status

        # Cuántos temas futuros desbloquea este nodo (valor estratégico en el DAG)
        unlocks = [
            other["id"] for other in TOPICS if tid in other["prereqs"]
        ]
        implicit_targets = get_Transitive_Encompassed(tid)

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
                "encompasses": t["encompasses"],
                "implicit_targets": implicit_targets,
                "unlocks": unlocks,
                "status": status,
                "mastery": round(mastery, 2),
                "retention": ret_info["retention"],
                "stability_days": round(float(st.get("stability_days", 2.0)), 1),
                "repetitions": int(st.get("repetitions", 0)),
                "due_for_review": ret_info["due_for_review"],
            }
        )

    # Construir la Cola de Tareas Adaptativas (Math Academy Task Queue)
    recommendations = build_recommendations(enriched_topics, profile["current_semester"])

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

    return {
        "storage_backend": get_storage_backend_name(),
        "profile": profile,
        "courses": course_summaries,
        "topics": enriched_topics,
        "recommendations": recommendations,
        "activity_7d": seven_days,
    }


def build_recommendations(enriched_topics, current_semester):
    """
    Selecciona hasta 4 tareas óptimas combinando:
    1. Repasos FIRe que consolidan múltiples nodos anteriores (Encompassing).
    2. Lecciones de la frontera del semestre actual (Semestre 1-2).
    3. Lecciones de anticipación estratégica (Semestres siguientes desbloqueados).
    """
    by_id = {t["id"]: t for t in enriched_topics}
    due_ids = {t["id"] for t in enriched_topics if t["status"] == "review_due"}

    tasks = []

    # 1. ¿Hay una lección nueva disponible o repaso superior que cubra implícitamente los repasos pendientes?
    candidates = [
        t
        for t in enriched_topics
        if t["status"] in ("available", "in_progress", "review_due")
    ]

    def score_candidate(t):
        # Cuántos repasos vencidos absorbe implícitamente
        covered_due = sum(
            w for sub_id, w in t["implicit_targets"].items() if sub_id in due_ids
        )
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

        unlock_bonus = 0.35 * len(t["unlocks"])
        return status_bonus + sem_bonus + (2.5 * covered_due) + unlock_bonus

    ranked = sorted(candidates, key=score_candidate, reverse=True)

    covered_implicitly = set()
    for t in ranked:
        if t["id"] in covered_implicitly and t["status"] == "review_due":
            continue
        implicit_list = [
            {"id": sub_id, "title": by_id[sub_id]["title"], "weight": w}
            for sub_id, w in t["implicit_targets"].items()
            if sub_id in by_id
        ]
        for sub_id, w in t["implicit_targets"].items():
            if w >= 0.5:
                covered_implicitly.add(sub_id)

        if t["status"] == "review_due":
            task_type = "review"
            tag_label = "Repaso Espaciado FIRe"
        elif t["semester"] > current_semester:
            task_type = "anticipation"
            tag_label = f"Anticipación Semestre {t['semester']}"
        else:
            task_type = "lesson"
            tag_label = f"Frontera Semestre {t['semester']}"

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
                "xp": t["xp"] if task_type != "review" else max(6, int(t["xp"] * 0.7)),
                "estimated_mins": t["estimated_mins"],
                "mastery": t["mastery"],
                "retention": t["retention"],
                "unlocks_count": len(t["unlocks"]),
                "implicit_rep_topics": implicit_list,
            }
        )
        if len(tasks) >= 4:
            break

    # Si todos los temas están dominados y ninguno vence hoy, ofrecer práctica de refuerzo/velocidad
    if not tasks:
        for t in enriched_topics[:3]:
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
                    "xp": 8,
                    "estimated_mins": 6,
                    "mastery": t["mastery"],
                    "retention": t["retention"],
                    "unlocks_count": len(t["unlocks"]),
                    "implicit_rep_topics": [],
                }
            )

    return tasks


def get_topic_lesson_payload(topic_id):
    """Devuelve la lección completa con preguntas curadas + preguntas paramétricas generadas al vuelo."""
    t = TOPICS_BY_ID.get(topic_id)
    if not t:
        return None
    course = COURSES_BY_ID[t["course_id"]]
    dynamic_qs = generate_parametric_questions(t["generator_type"], count=2)
    curated_qs = [dict(q, is_parametric=False) for q in t["questions"]]
    all_questions = curated_qs + dynamic_qs

    implicit_map = get_Transitive_Encompassed(topic_id)
    implicit_details = [
        {"id": sid, "title": TOPICS_BY_ID[sid]["title"], "weight": w}
        for sid, w in implicit_map.items()
        if sid in TOPICS_BY_ID
    ]

    return {
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
        "implicit_details": implicit_details,
        "theory": t["theory"],
        "ds_connection": t["ds_connection"],
        "uc_exam_tip": t["uc_exam_tip"],
        "worked_example": t["worked_example"],
        "questions": all_questions,
    }


def record_completion(topic_id, correct_count, total_count, task_type="lesson"):
    """
    Actualiza la maestría del nodo practicado y propaga crédito de repetición implícita
    fraccionaria (FIRe) hacia los nodos prerrequisito en el grafo.
    """
    init_db()
    if topic_id not in TOPICS_BY_ID:
        raise ValueError("Tópico no encontrado")

    topic = TOPICS_BY_ID[topic_id]
    total_count = max(1, int(total_count))
    correct_count = max(0, min(total_count, int(correct_count)))
    score_ratio = correct_count / total_count
    passed = score_ratio >= 0.65

    now_ts = datetime.datetime.now().timestamp()
    today_str = datetime.date.today().isoformat()

    conn = get_conn()
    cur = conn.cursor()

    st = dict(
        cur.execute(
            "SELECT * FROM topic_state WHERE topic_id = ?", (topic_id,)
        ).fetchone()
    )
    old_mastery = float(st["mastery"])
    old_stability = max(1.5, float(st["stability_days"]))
    reps = int(st["repetitions"])

    if passed:
        new_mastery = min(1.0, max(old_mastery, 0.72 + 0.28 * score_ratio))
        growth_factor = 1.8 + 0.9 * score_ratio
        new_stability = min(90.0, old_stability * growth_factor if reps > 0 else 3.5)
        new_reps = reps + 1
    else:
        # Penalización suave y re-agendamiento inmediato
        new_mastery = max(0.25, old_mastery * 0.75 if old_mastery > 0 else 0.35)
        new_stability = max(1.0, old_stability * 0.6)
        new_reps = reps

    next_review_ts = now_ts + new_stability * 86400.0
    cur.execute(
        """
        UPDATE topic_state
        SET mastery = ?,
            stability_days = ?,
            repetitions = ?,
            last_practiced_ts = ?,
            next_review_ts = ?,
            total_attempts = total_attempts + ?,
            correct_attempts = correct_attempts + ?
        WHERE topic_id = ?
        """,
        (
            new_mastery,
            new_stability,
            new_reps,
            now_ts,
            next_review_ts,
            total_count,
            correct_count,
            topic_id,
        ),
    )

    # Propagación FIRe (Fractional Implicit Repetition) a sub-tópicos abarcados
    implicit_boosted = []
    if passed:
        implicit_weights = get_Transitive_Encompassed(topic_id)
        for sub_id, weight in implicit_weights.items():
            sub_row = cur.execute(
                "SELECT * FROM topic_state WHERE topic_id = ?", (sub_id,)
            ).fetchone()
            if not sub_row:
                continue
            sub_m = float(sub_row["mastery"])
            sub_s = max(1.5, float(sub_row["stability_days"]))
            if sub_m > 0.0:
                boosted_s = min(90.0, sub_s * (1.0 + 0.55 * weight * score_ratio))
                boosted_m = min(1.0, max(sub_m, sub_m + 0.12 * weight))
                sub_next_ts = now_ts + boosted_s * 86400.0
                cur.execute(
                    """
                    UPDATE topic_state
                    SET mastery = ?, stability_days = ?, last_practiced_ts = ?, next_review_ts = ?
                    WHERE topic_id = ?
                    """,
                    (boosted_m, boosted_s, now_ts, sub_next_ts, sub_id),
                )
                implicit_boosted.append(
                    {
                        "id": sub_id,
                        "title": TOPICS_BY_ID[sub_id]["title"],
                        "weight": weight,
                        "new_stability_days": round(boosted_s, 1),
                    }
                )

    # Cálculo de XP (Math Academy otorga XP completo al aprobar y bono por perfección)
    base_xp = int(topic["xp"])
    if passed:
        xp_earned = base_xp + (3 if score_ratio == 1.0 else 0)
    else:
        xp_earned = max(2, int(base_xp * 0.25 * score_ratio))

    cur.execute(
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
            now_ts,
        ),
    )

    cur.execute(
        """
        UPDATE user_profile
        SET total_xp = total_xp + ?, last_active_date = ?
        WHERE id = 1
        """,
        (xp_earned, today_str),
    )

    conn.commit()
    conn.close()

    return {
        "passed": passed,
        "score_ratio": round(score_ratio, 2),
        "xp_earned": xp_earned,
        "new_mastery": round(new_mastery, 2),
        "new_stability_days": round(new_stability, 1),
        "implicit_boosted": implicit_boosted,
    }


def get_diagnostic_questions():
    """
    Genera un Diagnóstico Adaptativo Inicial de 6 preguntas clave del Semestre 1 y 2
    para calibrar la frontera de conocimiento del estudiante.
    """
    diag_topic_ids = [
        "ic_desigualdades",
        "iag_logica_conjuntos",
        "ic_limites",
        "iag_induccion_sumatorias",
        "iag_vectores_geometria",
        "tme_combinatoria_descriptiva",
    ]
    items = []
    for tid in diag_topic_ids:
        t = TOPICS_BY_ID[tid]
        q = dict(t["questions"][0])
        items.append(
            {
                "topic_id": tid,
                "topic_title": t["title"],
                "course_name": COURSES_BY_ID[t["course_id"]]["name"],
                "semester": t["semester"],
                "question": q,
            }
        )
    return items


def apply_diagnostic_results(results_by_topic, target_semester=1):
    """
    Calibra el grafo según las respuestas del diagnóstico inicial, propagando también
    maestría hacia los prerrequisitos de los temas aprobados.
    """
    init_db()
    now_ts = datetime.datetime.now().timestamp()
    today_str = datetime.date.today().isoformat()
    conn = get_conn()
    cur = conn.cursor()

    mastered_ids = set()
    for tid, is_correct in results_by_topic.items():
        if is_correct and tid in TOPICS_BY_ID:
            mastered_ids.add(tid)
            for p in TOPICS_BY_ID[tid]["prereqs"]:
                mastered_ids.add(p)

    for tid in mastered_ids:
        cur.execute(
            """
            UPDATE topic_state
            SET mastery = 0.88,
                stability_days = 6.0,
                repetitions = MAX(repetitions, 1),
                last_practiced_ts = ?,
                next_review_ts = ?
            WHERE topic_id = ?
            """,
            (now_ts, now_ts + 6.0 * 86400.0, tid),
        )

    xp_bonus = len(mastered_ids) * 10
    if xp_bonus > 0:
        cur.execute(
            """
            INSERT INTO xp_log (date_str, topic_id, task_type, xp_earned, score_ratio, implicit_topics_json, created_ts)
            VALUES (?, 'diagnostic', 'diagnostic', ?, 1.0, '[]', ?)
            """,
            (today_str, xp_bonus, now_ts),
        )

    cur.execute(
        """
        UPDATE user_profile
        SET diagnostic_completed = 1,
            current_semester = ?,
            total_xp = total_xp + ?,
            last_active_date = ?
        WHERE id = 1
        """,
        (int(target_semester), xp_bonus, today_str),
    )
    conn.commit()
    conn.close()
    return {"mastered_count": len(mastered_ids), "xp_bonus": xp_bonus}


def update_profile_settings(current_semester=None, daily_goal_xp=None, preset_mode=None):
    """Actualiza preferencias o aplica un preset rápido (ej. Mitad Semestre 1, Fin Semestre 1, Reset)."""
    init_db()
    now_ts = datetime.datetime.now().timestamp()
    conn = get_conn()
    cur = conn.cursor()

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
            "UPDATE user_profile SET total_xp = 0, diagnostic_completed = 0, current_semester = 1 WHERE id = 1"
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
            "UPDATE user_profile SET current_semester = 1, diagnostic_completed = 1, total_xp = MAX(total_xp, 45) WHERE id = 1"
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
            "UPDATE user_profile SET current_semester = 2, diagnostic_completed = 1, total_xp = MAX(total_xp, 100) WHERE id = 1"
        )

    conn.commit()
    conn.close()
    return get_full_state()


def export_backup_payload():
    """Exporta todo el progreso (perfil, estado de nodos y registro XP) en un JSON portable."""
    init_db()
    conn = get_conn()
    cur = conn.cursor()
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
    }


def import_backup_payload(payload):
    """Restaura un respaldo JSON en la base de datos activa (Cloud o Local)."""
    init_db()
    conn = get_conn()
    cur = conn.cursor()

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

    conn.commit()
    conn.close()
    return get_full_state()
