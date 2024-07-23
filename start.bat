@echo off

if not exist ".\env" (
    echo Environment not found. Installing Miniconda...
    call .\install\install.bat
    if errorlevel 1 (
        echo Installation failed. Please check the error messages above.
        exit /b 1
    )
)

echo Running main.py with the installed Python...

streamlit run /home/wxy/code/ak_code_library/web.py