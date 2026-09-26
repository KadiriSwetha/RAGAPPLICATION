@echo off
REM Batch script to start FastAPI, Inngest server, and Streamlit app

echo Starting RAG Application Services...
echo ====================================

REM Install/Update Python packages
echo [1/4] Checking Python packages...
call .venv\Scripts\activate

REM Check if key packages are installed
python -c "import fastapi, inngest, streamlit" 2>nul
if %errorlevel% neq 0 (
    echo Installing missing Python packages...
    pip install -q --upgrade pip
    pip install -q -r requirements.txt 2>nul || uv pip install -e .
    echo Python packages installed!
) else (
    echo Python packages already installed, skipping...
)

REM Install/Update NPM packages for Inngest
echo [2/4] Checking Inngest CLI...
call npm list -g inngest-cli >nul 2>&1 || echo Inngest CLI will be installed via npx

echo.
echo ====================================
echo Starting services...
echo ====================================

REM Start Ollama server in a new window
echo [1/5] Starting Ollama server...
start "Ollama Server" cmd /k "ollama serve"

REM Wait 2 seconds for Ollama to initialize
timeout /t 2 /nobreak >nul

REM Start FastAPI server in a new window
echo [2/5] Starting FastAPI server...
start "FastAPI Server" cmd /k ".venv\Scripts\activate && uvicorn main:app --reload --port 8000"

REM Wait 3 seconds for FastAPI to initialize
timeout /t 3 /nobreak >nul

REM Start Inngest Dev Server in a new window
echo [3/5] Starting Inngest Dev Server...
REM --no-discovery + explicit -u avoid scanning other ports; --poll-interval 30 avoids
REM the default 5s poll causing the Dev Server UI to look stuck "syncing" continuously
start "Inngest Dev Server" cmd /k "npx inngest-cli@latest dev --no-discovery --poll-interval 30 -u http://127.0.0.1:8000/api/inngest"

REM Wait 3 seconds for Inngest to initialize
timeout /t 3 /nobreak >nul

REM Start Streamlit app in a new window
echo [4/5] Starting Streamlit app...
start "Streamlit App" cmd /k ".venv\Scripts\activate && streamlit run streamlit_app.py"

echo.
echo ====================================
echo All services started successfully!
echo ====================================
echo.
echo Ollama:         http://localhost:11434
echo FastAPI:        http://localhost:8000
echo Inngest:        http://localhost:8288
echo Streamlit:      http://localhost:8501
echo.
echo Press any key to close this window (services will continue running)...
pause >nul
