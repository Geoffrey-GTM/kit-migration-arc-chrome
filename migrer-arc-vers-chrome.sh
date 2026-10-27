#!/bin/bash
# ==================================================================
#  Migration Arc -> Google Chrome (macOS)
#  Lanceur : vérifie l'environnement puis exécute migrer_arc_chrome.py.
#
#  Usage   : bash migrer-arc-vers-chrome.sh [--mode espaces|unique] [--profil "Nom"] [--remplacer] [--dossiers] [--forcer]
#            bash migrer-arc-vers-chrome.sh --diagnostic   (lecture seule)
#  Aide    : bash migrer-arc-vers-chrome.sh --aide
#  Mode d'emploi complet : LISEZMOI.txt
# ==================================================================

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_SCRIPT="$KIT_DIR/migrer_arc_chrome.py"

if [ "$(uname)" != "Darwin" ]; then
  echo "✗ Ce script fonctionne uniquement sur Mac."
  exit 1
fi
if [ ! -f "$PY_SCRIPT" ]; then
  echo "✗ migrer_arc_chrome.py est introuvable : il doit être dans le même dossier que ce script."
  exit 1
fi

case " $* " in
  *" --aide "*|*" --help "*|*" -h "*|*" --version "*|*" --diagnostic "*) ;;  # lecture seule : navigateurs ouverts acceptés
  *)
    if pgrep -x "Arc" >/dev/null 2>&1; then
      echo "✗ Arc est ouvert : quitte-le (Cmd+Q) puis relance."
      exit 1
    fi
    if pgrep -x "Google Chrome" >/dev/null 2>&1; then
      echo "✗ Chrome est ouvert : quitte-le (Cmd+Q) puis relance."
      exit 1
    fi
    ;;
esac

PY=""
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if [ -x "$candidate" ]; then
    PY="$candidate"
    break
  fi
done
if [ -z "$PY" ] && xcode-select -p >/dev/null 2>&1 && [ -x /usr/bin/python3 ]; then
  PY=/usr/bin/python3
fi
if [ -z "$PY" ]; then
  echo "✗ Python 3 manquant : lance « xcode-select --install », accepte l'installation, puis relance."
  exit 1
fi

export KIT_DIR
exec "$PY" -I -B "$PY_SCRIPT" "$@"
