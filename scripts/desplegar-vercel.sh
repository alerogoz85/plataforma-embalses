#!/usr/bin/env bash
# Publica la API (backend) en Vercel con la base de datos actual.
#
# Uso:  scripts/desplegar-vercel.sh
#
# El sitio (frontend) NO se publica con este script: se despliega solo por Git
# (cada merge a main es un despliegue de producción; cada PR, una vista previa).
# La API sí se publica por CLI porque la base de datos no está en el repositorio.
#
# Requisitos: Vercel CLI con sesión iniciada (`vercel login`) y la base cargada
# en data/hidrologia.duckdb (ver README).
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
base="$raiz/data/hidrologia.duckdb"
[[ -f "$base" ]] || { echo "Falta $base: ejecuta antes la sincronización." >&2; exit 1; }

# `vercel link` agrega un token OIDC temporal a .env.local; se retira para no
# dejarlo en disco (ni arriesgar que se suba a git). Si el archivo queda vacío, se borra.
retirar_token_local() {
  [[ -f .env.local ]] || return 0
  sed -i.bak '/^# Created by Vercel CLI/,$d' .env.local && rm -f .env.local.bak
  [[ -s .env.local ]] || rm -f .env.local
}

mkdir -p "$raiz/backend/data"
cp "$base" "$raiz/backend/data/hidrologia.duckdb"
cd "$raiz/backend"
vercel link --yes --project plataforma-embalses-api >/dev/null
retirar_token_local
vercel deploy --prod --yes
