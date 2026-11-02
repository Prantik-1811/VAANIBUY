@echo off
setlocal
echo [1/3] Creating local Python environment...
if not exist .venv (
    py -m venv .venv
    if errorlevel 1 goto error
) else (
    echo .venv already exists. Reusing it.
)
echo [2/3] Installing Python packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo [3/3] Preparing .env...
if not exist .env copy .env.example .env
echo.
echo Setup complete.
echo Next: run "notepad .env" and paste your Sarvam API key.
echo Then run "run.cmd".
goto end
:error
echo Setup failed. Check the error above.
exit /b 1
:end
endlocal
