#!/bin/bash
# run_bot.sh - Wrapper to run browser_bot.py in a virtual environment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_DIR="$SCRIPT_DIR/../venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    virtualenv "$VENV_DIR" > /dev/null
    source "$VENV_DIR/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt" > /dev/null
else
    source "$VENV_DIR/bin/activate"
fi

python3 "$SCRIPT_DIR/browser_bot.py" "$@"
