#!/usr/bin/env bash
# Publica la aplicación en Vercel: la API (backend) y el sitio (frontend).
#
# Uso:  scripts/desplegar-vercel.sh [api|web|todo]      (por defecto: todo)
#
# Requisitos: Vercel CLI con sesión iniciada (`vercel login`) y, para publicar
# la API, la base de datos cargada en data/hidrologia.duckdb (ver README).
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
objetivo="${1:-todo}"

# `vercel link` agrega un token OIDC temporal a .env.local; se retira para no
# dejarlo en disco (ni arriesgar que se suba a git). Si el archivo queda vacío, se borra.
retirar_token_local() {
  [[ -f .env.local ]] || return 0
  sed -i.bak '/^# Created by Vercel CLI/,$d' .env.local && rm -f .env.local.bak
  [[ -s .env.local ]] || rm -f .env.local
}

desplegar_api() {
  local base="$raiz/data/hidrologia.duckdb"
  [[ -f "$base" ]] || { echo "Falta $base: ejecuta antes la sincronización." >&2; exit 1; }
  mkdir -p "$raiz/backend/data"
  cp "$base" "$raiz/backend/data/hidrologia.duckdb"
  ( cd "$raiz/backend"
    vercel link --yes --project plataforma-embalses-api >/dev/null
    retirar_token_local
    vercel deploy --prod --yes )
}

desplegar_web() {
  ( cd "$raiz/frontend"
    vercel link --yes --project plataforma-embalses >/dev/null
    retirar_token_local
    vercel deploy --prod --yes )
}

case "$objetivo" in
  api)  desplegar_api ;;
  web)  desplegar_web ;;
  todo) desplegar_api; desplegar_web ;;
  *)    echo "Uso: $0 [api|web|todo]" >&2; exit 2 ;;
esac
