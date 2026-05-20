#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../frontend"
export PATH="$HOME/.nvm/versions/node/v24.15.0/bin:$PATH"
npm run dev -- --host 0.0.0.0

