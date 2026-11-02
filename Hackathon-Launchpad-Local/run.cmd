@echo off
if not exist .venv\Scripts\python.exe (
    echo Environment missing. Run setup.cmd first.
    pause
    exit /b 1
)
.venv\Scripts\python.exe test_sarvam.py
pause
