#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "============================"
echo "AIGenerator macOS Launcher"
echo "============================"

# Homebrew's Python ships tkinter as a separate formula (python-tk).
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c "import tkinter" >/dev/null 2>&1; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "Python 3 with tkinter is required."
        echo "Install it from https://www.python.org/downloads/ (includes tkinter) and run this again."
        exit 1
    fi
    echo "Installing Python and tkinter..."
    brew install python python-tk
fi

python3 setup.py
