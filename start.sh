#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: docker compose is not available."
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

required_vars=(
  "SPOTIFY_CLIENT_ID"
  "SPOTIFY_CLIENT_SECRET"
  "SPOTIFY_REDIRECT_URI"
)

missing=()
for var in "${required_vars[@]}"; do
  value="$(grep -E "^${var}=" .env | sed -E "s/^${var}=//" || true)"
  if [[ -z "${value}" ]]; then
    missing+=("$var")
  fi
done

if ! grep -qE '^FERNET_KEY=' .env || [[ -z "$(grep -E '^FERNET_KEY=' .env | sed -E 's/^FERNET_KEY=//')" ]]; then
  if command -v python >/dev/null 2>&1; then
    key="$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || true)"
    if [[ -n "$key" ]]; then
      if grep -qE '^FERNET_KEY=' .env; then
        sed -i.bak -E "s|^FERNET_KEY=.*$|FERNET_KEY=$key|" .env && rm -f .env.bak
      else
        printf "\nFERNET_KEY=%s\n" "$key" >> .env
      fi
      echo "Generated and set FERNET_KEY in .env"
    fi
  fi
fi

if ! grep -qE '^FERNET_KEY=' .env || [[ -z "$(grep -E '^FERNET_KEY=' .env | sed -E 's/^FERNET_KEY=//')" ]]; then
  missing+=("FERNET_KEY")
fi

if (( ${#missing[@]} > 0 )); then
  echo "Please set the following in .env before starting:"
  for var in "${missing[@]}"; do
    echo "  - $var"
  done
  exit 1
fi

docker compose up --build
