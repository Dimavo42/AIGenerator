Ollama AI Launcher

This project provides a launcher for running the Ollama AI application on Windows, macOS and Linux.

Each start script checks for Python, then hands over to setup.py, which will:

1) Install Ollama if it is missing
2) Create a local .venv virtual environment
3) Install the required Python packages from requirements.txt (again only when it changes)
4) Launch the Python GUI application (app.py) without keeping the terminal window open


Installation:
1) Open the folder where you want to download the project.
2) Open a terminal in that folder, or use the cd command to navigate to it.
3) Clone the repository:                                 git clone https://github.com/Dimavo42/AIGenerator.git
4) Open the cloned AIGenerator folder.
5) Start the launcher for your system:
   - Windows: double-click start_windows.bat
   - macOS:   double-click start_macos.command
   - Linux:   run ./start_linux.sh
