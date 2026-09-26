@echo off
echo ================================================
echo Installing Missing Dependencies
echo ================================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing llama-index packages...
python -m pip install llama-index-core
python -m pip install llama-index-readers-file

echo.
echo ================================================
echo Verifying installation...
echo ================================================
python -c "from llama_index.readers.file import PDFReader; from llama_index.core.node_parser import SentenceSplitter; print('SUCCESS: llama-index packages installed correctly!')" 2>&1

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo Installation Complete!
    echo ================================================
    echo You can now run: start_services.bat
) else (
    echo.
    echo ================================================
    echo ERROR: Installation failed!
    echo ================================================
    echo Please check the error messages above.
)

echo.
pause
