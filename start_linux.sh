#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "============================"
echo "AIGenerator Linux Launcher"
echo "============================"

# The app needs Python 3 with venv and tkinter - on Linux those are separate packages.
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c "import venv, ensurepip, tkinter" >/dev/null 2>&1; then
    echo "Installing Python 3, venv and tkinter..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip python3-tk curl
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip python3-tkinter curl
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm python python-pip tk curl
    else
        echo "Unknown package manager. Install Python 3 with venv and tkinter, then run this again."
        exit 1
    fi
fi

python3 setup.py
