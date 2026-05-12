#!/usr/bin/env bash
set -euo pipefail

echo "[1/8] Resolviendo el directorio del script..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[2/8] Moviéndome al root del proyecto: ${SCRIPT_DIR}"
cd "${SCRIPT_DIR}"

if [ ! -d ".venv" ]; then
  echo "[3/8] .venv no existe. Creando entorno virtual..."
  python3 -m venv .venv
else
  echo "[3/8] .venv ya existe. Reutilizando entorno virtual..."
fi

echo "[4/8] Activando entorno virtual..."
source .venv/bin/activate

echo "[5/8] Actualizando pip..."
python -m pip install --upgrade pip

echo "[6/8] Instalando proyecto en modo editable..."
pip install -e .

echo "[7/8] Iniciando servidor Uvicorn en 0.0.0.0:8000..."
echo "[8/8] Presiona Ctrl+C para detener el servidor."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
