#!/bin/bash
set -euo pipefail

# === CONFIGURAZIONE ===
CONFIG=(
  "backend/.env /home/backend/culturallm-backend/backend/.env"
  "mariadb/.env /home/backend/culturallm-backend/mariadb/.env"
  "nlp/.env /home/backend/culturallm-backend/nlp/.env"
)

# === FLAG / VARIABILI ===
VPS_USER=""
VPS_HOST=""
MODE_PUSH=false
MODE_PULL=false
LOAD_GH=false
LOAD_VPS=false

# === PARSING ARGOMENTI ===
while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) MODE_PUSH=true; shift ;;
    --pull) MODE_PULL=true; shift ;;
    --gh)   LOAD_GH=true; shift ;;
    --vps)  LOAD_VPS=true; shift ;;
    -u|--user) VPS_USER="$2"; shift 2 ;;
    -h|--host) VPS_HOST="$2"; shift 2 ;;
    *) echo "❌ Uso: $0 --push|--pull [--gh] [--vps] [-u user] [-h host]"; exit 1 ;;
  esac
done

# === VALIDAZIONI ===
if ! $MODE_PUSH && ! $MODE_PULL; then
  echo "❌ Errore: specifica almeno uno tra --push o --pull." >&2
  exit 1
fi

if $LOAD_VPS || $MODE_PULL; then
  if [[ -z "${VPS_USER:-}" || -z "${VPS_HOST:-}" ]]; then
    echo "❌ Errore: --vps o --pull richiedono -u <user> e -h <host>." >&2
    exit 1
  fi
fi

# === PULL: VPS → LOCAL ===
if $MODE_PULL; then
  echo "📥 Pull .env da VPS..."
  for entry in "${CONFIG[@]}"; do
    LOCAL_FILE=${entry%% *}
    REMOTE_FILE=${entry##* }

    echo "➡️  Scarico $REMOTE_FILE → $LOCAL_FILE"
    scp -q "$VPS_USER@$VPS_HOST:$REMOTE_FILE" "$LOCAL_FILE"
    echo "✅ Scaricato $LOCAL_FILE"
  done
fi

# === PUSH: LOCAL → VPS / GITHUB ===
if $MODE_PUSH; then
  for entry in "${CONFIG[@]}"; do
    ENV_FILE=${entry%% *}
    REMOTE_PATH=${entry##* }

    if [[ ! -f "$ENV_FILE" ]]; then
      echo "⚠️  $ENV_FILE non trovato, salto."
      continue
    fi

    if $LOAD_GH; then
      dir_name=$(dirname "$ENV_FILE")
      secret_key="ENV_$(basename "$dir_name" | tr '[:lower:]' '[:upper:]')"

      base64_content=$(base64 -w 0 "$ENV_FILE")

      echo "🔐 Carico $ENV_FILE come secret $secret_key"
      gh secret set "$secret_key" --body "$base64_content" &>/dev/null
      echo "✅ GitHub secret: $secret_key"
    fi


    if $LOAD_VPS; then
      echo "📡 Copia su VPS: $ENV_FILE → $VPS_USER@$VPS_HOST:$REMOTE_PATH"
      scp -q "$ENV_FILE" "$VPS_USER@$VPS_HOST:$REMOTE_PATH"
      echo "✅ VPS ok"
    fi
  done
fi

echo "🏁 Sincronizzazione completata!"