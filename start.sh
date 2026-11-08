#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8765}"

if ss -ltn "sport = :$PORT" 2>/dev/null | grep -q ":$PORT "; then
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  echo "============================================================"
  echo "  Math Academy UC — Lic. Ingeniería en Ciencia de Datos"
  echo "  Local:   http://127.0.0.1:$PORT"
  if [ -n "$LAN_IP" ]; then
    echo "  Red LAN: http://$LAN_IP:$PORT"
  fi
  echo "  (Haz Ctrl+clic sobre la dirección para abrir en el navegador)"
  echo "============================================================"
  read -rp "Presiona Enter para cerrar esta ventana o Ctrl+C para salir..."
  exit 0
fi

python3 "$DIR/app.py" "$PORT" || {
  echo ""
  read -rp "El servidor se detuvo. Presiona Enter para cerrar..."
}
