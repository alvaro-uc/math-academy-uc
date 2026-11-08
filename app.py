#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Local para Math Academy UC — Ingeniería en Ciencia de Datos
Cero dependencias externas (usa Python stdlib `http.server` + `sqlite3`).
"""

import json
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")


def _dispatch_request(method, path, raw_body=b""):
    """Despachador común para BaseHTTPRequestHandler local y WSGI (Vercel)."""
    if method == "GET":
        if path == "/api/state":
            st = engine.get_full_state()
            if st["profile"]["total_xp"] == 0 and st["profile"]["diagnostic_completed"] == 0:
                st = engine.update_profile_settings(preset_mode="mid_sem1")
            return 200, "application/json; charset=utf-8", json.dumps(st, ensure_ascii=False).encode("utf-8")

        if path == "/api/backup":
            return 200, "application/json; charset=utf-8", json.dumps(engine.export_backup_payload(), ensure_ascii=False).encode("utf-8")

        if path.startswith("/api/topic/"):
            topic_id = path.split("/api/topic/", 1)[1].strip("/")
            payload = engine.get_topic_lesson_payload(topic_id)
            if not payload:
                return 404, "application/json; charset=utf-8", json.dumps({"error": "Tópico no encontrado"}, ensure_ascii=False).encode("utf-8")
            return 200, "application/json; charset=utf-8", json.dumps(payload, ensure_ascii=False).encode("utf-8")

        if path == "/api/diagnostic":
            return 200, "application/json; charset=utf-8", json.dumps({"items": engine.get_diagnostic_questions()}, ensure_ascii=False).encode("utf-8")

        # Servir archivos estáticos
        if path in ("/", "/index.html", "/api", "/api/index.py"):
            file_path = os.path.join(STATIC_DIR, "index.html")
        elif path.startswith("/assets/"):
            rel = path.lstrip("/")
            file_path = os.path.join(BASE_DIR, rel)
        else:
            rel = path.lstrip("/")
            file_path = os.path.join(STATIC_DIR, rel)

        file_path = os.path.abspath(file_path)
        if not (file_path.startswith(STATIC_DIR) or file_path.startswith(os.path.join(BASE_DIR, "assets"))):
            return 403, "text/plain; charset=utf-8", b"Forbidden"

        if not os.path.isfile(file_path):
            return 404, "text/plain; charset=utf-8", b"Not Found"

        ctype, _ = mimetypes.guess_type(file_path)
        ctype = ctype or "application/octet-stream"
        with open(file_path, "rb") as f:
            data = f.read()
        return 200, ctype, data

    if method == "POST":
        try:
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception as exc:
            return 400, "application/json; charset=utf-8", json.dumps({"error": f"JSON inválido: {exc}"}, ensure_ascii=False).encode("utf-8")

        if path == "/api/complete":
            topic_id = body.get("topic_id")
            correct_count = body.get("correct_count", 0)
            total_count = body.get("total_count", 1)
            task_type = body.get("task_type", "lesson")
            try:
                res = engine.record_completion(topic_id, correct_count, total_count, task_type)
                return 200, "application/json; charset=utf-8", json.dumps({"result": res, "state": engine.get_full_state()}, ensure_ascii=False).encode("utf-8")
            except Exception as exc:
                return 400, "application/json; charset=utf-8", json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")

        if path == "/api/diagnostic":
            results = body.get("results", {})
            target_semester = body.get("target_semester", 1)
            res = engine.apply_diagnostic_results(results, target_semester)
            return 200, "application/json; charset=utf-8", json.dumps({"result": res, "state": engine.get_full_state()}, ensure_ascii=False).encode("utf-8")

        if path == "/api/profile":
            state = engine.update_profile_settings(
                current_semester=body.get("current_semester"),
                daily_goal_xp=body.get("daily_goal_xp"),
                preset_mode=body.get("preset_mode"),
            )
            return 200, "application/json; charset=utf-8", json.dumps({"state": state}, ensure_ascii=False).encode("utf-8")

        if path == "/api/backup":
            try:
                state = engine.import_backup_payload(body)
                return 200, "application/json; charset=utf-8", json.dumps({"state": state}, ensure_ascii=False).encode("utf-8")
            except Exception as exc:
                return 400, "application/json; charset=utf-8", json.dumps({"error": f"Error al restaurar respaldo: {exc}"}, ensure_ascii=False).encode("utf-8")

        return 404, "application/json; charset=utf-8", json.dumps({"error": "Ruta no encontrada"}, ensure_ascii=False).encode("utf-8")

    return 405, "text/plain; charset=utf-8", b"Method Not Allowed"


class handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if self.path.startswith("/api/"):
            sys.stderr.write(f"[MathAcademy API] {self.command} {self.path}\n")

    def _handle(self, method):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0")) if method == "POST" else 0
        raw_body = self.rfile.read(length) if length > 0 else b""
        status, ctype, data = _dispatch_request(method, parsed.path, raw_body)
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if ctype.startswith("application/json"):
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


MathAcademyHandler = handler


def app(environ, start_response):
    """Aplicación WSGI estándar para Vercel Python Runtime."""
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = (
        environ.get("HTTP_X_MATCHED_PATH")
        or environ.get("REQUEST_URI", "").split("?", 1)[0]
        or environ.get("PATH_INFO", "/")
    )
    try:
        length = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError:
        length = 0
    raw_body = environ["wsgi.input"].read(length) if length > 0 and "wsgi.input" in environ else b""
    status_code, ctype, data = _dispatch_request(method, path, raw_body)
    status_map = {
        200: "200 OK",
        400: "400 Bad Request",
        403: "403 Forbidden",
        404: "404 Not Found",
        405: "405 Method Not Allowed",
        500: "500 Internal Server Error",
    }
    headers = [
        ("Content-Type", ctype),
        ("Content-Length", str(len(data))),
    ]
    if ctype.startswith("application/json"):
        headers.append(("Cache-Control", "no-store"))
    start_response(status_map.get(status_code, f"{status_code} OK"), headers)
    return [data]


application = app


def run_server(port=8765):
    engine.init_db()
    # Si la base de datos está recién inicializada sin actividad, cargamos el preset inicial "mid_sem1"
    # para que el usuario vea inmediatamente la frontera de Semestre 1 + FIRe activo,
    # pudiendo recalibrar con el Diagnóstico o reiniciar desde 0 con un clic.
    st = engine.get_full_state()
    if st["profile"]["total_xp"] == 0 and st["profile"]["diagnostic_completed"] == 0:
        engine.update_profile_settings(preset_mode="mid_sem1")

    import socket
    lan_ip = "127.0.0.1"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
    except Exception:
        pass

    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("0.0.0.0", port), MathAcademyHandler)
    print(f"============================================================")
    print(f"  Math Academy UC — Lic. Ingeniería en Ciencia de Datos")
    print(f"  Local:   http://127.0.0.1:{port}")
    if lan_ip != "127.0.0.1":
        print(f"  Red LAN: http://{lan_ip}:{port}")
    print(f"  (Haz Ctrl+clic sobre la dirección para abrir en el navegador)")
    print(f"============================================================", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando servidor...")
        server.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run_server(port_arg)
