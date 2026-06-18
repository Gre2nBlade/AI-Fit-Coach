#!/usr/bin/env bash
# Запуск бэкенда AI Fit Coach + публичный туннель (Cloudflare Tunnel).
# Делает сервер доступным с ЛЮБОГО Wi-Fi и мобильного интернета,
# а не только из домашней сети. Cloudflare работает в РФ.
#
# Подготовка (один раз):
#   Установи cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
#     Windows (winget):  winget install --id Cloudflare.cloudflared
#   Для быстрого туннеля (случайный *.trycloudflare.com адрес) РЕГИСТРАЦИЯ НЕ НУЖНА.
#
# Запуск:
#   # быстрый туннель (адрес случайный, меняется при каждом запуске):
#   bash scripts/serve-public.sh
#
#   # именованный туннель со своим доменом в Cloudflare (адрес постоянный):
#   #   сначала разово настрой: cloudflared tunnel login && cloudflared tunnel create afc
#   #   и привяжи домен: cloudflared tunnel route dns afc afc.example.com
#   CF_TUNNEL=afc bash scripts/serve-public.sh
#
# Останов: Ctrl+C (остановит и туннель, и бэкенд).

set -euo pipefail

PORT="${API_PORT:-8000}"

cd "$(dirname "$0")/.."   # корень проекта

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "[!] cloudflared не найден. Установи его:"
  echo "    winget install --id Cloudflare.cloudflared"
  echo "    или https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
  exit 1
fi

# Активируем виртуальное окружение, если оно есть.
if [ -f "venv/Scripts/activate" ]; then
  # shellcheck disable=SC1091
  source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

echo "[*] Запускаю бэкенд на 0.0.0.0:${PORT} ..."
python -m backend.main &
BACKEND_PID=$!

# Гарантируем остановку бэкенда при выходе из скрипта.
cleanup() {
  echo ""
  echo "[*] Останавливаю бэкенд (pid ${BACKEND_PID}) ..."
  kill "${BACKEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Ждём, пока бэкенд поднимется.
sleep 3

if [ -n "${CF_TUNNEL:-}" ]; then
  echo "[*] Поднимаю именованный туннель '${CF_TUNNEL}' (постоянный адрес из настроек Cloudflare) ..."
  echo "    >> Впиши свой домен в frontend/www/js/config.js и выполни: cd frontend && npx cap sync android"
  cloudflared tunnel run "${CF_TUNNEL}"
else
  echo "[*] Поднимаю быстрый туннель к порту ${PORT} ..."
  echo "    Адрес случайный — смотри строку вида https://<...>.trycloudflare.com ниже"
  echo "    и впиши её в frontend/www/js/config.js, затем: cd frontend && npx cap sync android"
  cloudflared tunnel --url "http://localhost:${PORT}"
fi
