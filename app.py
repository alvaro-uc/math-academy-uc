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


class MathAcademyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Log limpio y silencioso para assets estáticos
        if self.path.startswith("/api/"):
            sys.stderr.write(f"[MathAcademy API] {self.command} {self.path}\n")

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/state":
            st = engine.get_full_state()
            if st["profile"]["total_xp"] == 0 and st["profile"]["diagnostic_completed"] == 0:
                st = engine.update_profile_settings(preset_mode="mid_sem1")
            self._send_json(st)
            return

        if path == "/api/backup":
            self._send_json(engine.export_backup_payload())
            return

        if path.startswith("/api/topic/"):
            topic_id = path.split("/api/topic/", 1)[1].strip("/")
            payload = engine.get_topic_lesson_payload(topic_id)
            if not payload:
                self._send_json({"error": "Tópico no encontrado"}, status=404)
            else:
                self._send_json(payload)
            return

        if path == "/api/diagnostic":
            self._send_json({"items": engine.get_diagnostic_questions()})
            return

        # Servir archivos estáticos
        if path in ("/", "/index.html"):
            file_path = os.path.join(STATIC_DIR, "index.html")
        elif path.startswith("/assets/"):
            rel = path.lstrip("/")
            file_path = os.path.join(BASE_DIR, rel)
        else:
            rel = path.lstrip("/")
            file_path = os.path.join(STATIC_DIR, rel)

        file_path = os.path.abspath(file_path)
        if not (file_path.startswith(STATIC_DIR) or file_path.startswith(os.path.join(BASE_DIR, "assets"))):
            self.send_error(403, "Forbidden")
            return

        if not os.path.isfile(file_path):
            self.send_error(404, "Not Found")
            return

        ctype, _ = mimetypes.guess_type(file_path)
        ctype = ctype or "application/octet-stream"
        with open(file_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            body = self._read_json_body()
        except Exception as exc:
            self._send_json({"error": f"JSON inválido: {exc}"}, status=400)
            return

        if path == "/api/complete":
            topic_id = body.get("topic_id")
            correct_count = body.get("correct_count", 0)
            total_count = body.get("total_count", 1)
            task_type = body.get("task_type", "lesson")
            try:
                res = engine.record_completion(topic_id, correct_count, total_count, task_type)
                self._send_json({"result": res, "state": engine.get_full_state()})
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=400)
            return

        if path == "/api/diagnostic":
            results = body.get("results", {})
            target_semester = body.get("target_semester", 1)
            res = engine.apply_diagnostic_results(results, target_semester)
            self._send_json({"result": res, "state": engine.get_full_state()})
            return

        if path == "/api/profile":
            state = engine.update_profile_settings(
                current_semester=body.get("current_semester"),
                daily_goal_xp=body.get("daily_goal_xp"),
                preset_mode=body.get("preset_mode"),
            )
            self._send_json({"state": state})
            return

        if path == "/api/backup":
            try:
                state = engine.import_backup_payload(body)
                self._send_json({"state": state})
            except Exception as exc:
                self._send_json({"error": f"Error al restaurar respaldo: {exc}"}, status=400)
            return

        self._send_json({"error": "Ruta no encontrada"}, status=404)


handler = MathAcademyHandler


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
