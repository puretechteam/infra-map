@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ============================================
echo  Infra Map - Dependency Installer
echo ============================================
echo.

set STEP=0
set PASS=0
set FAIL=0

echo [Step 1] Checking Python on PATH...
set STEP=1
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Python is available on PATH
    set /a PASS+=1
) else (
    echo   [FAIL] Python not found on PATH
    set /a FAIL+=1
)

echo.
echo [Step 2] Checking pip availability...
set STEP=2
python -m pip --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [OK] pip is available
    set /a PASS+=1
) else (
    echo   [FAIL] pip is not available
    set /a FAIL+=1
)

echo.
echo [Step 3] Installing requirements from requirements.txt...
set STEP=3
python -m pip install -r requirements.txt
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Requirements installed successfully
    set /a PASS+=1
) else (
    echo   [FAIL] Failed to install requirements
    set /a FAIL+=1
)

echo.
echo [Step 4] Checking PyInstaller...
set STEP=4
python -m PyInstaller --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [OK] PyInstaller is installed
    set /a PASS+=1
) else (
    echo   [INFO] PyInstaller not found, installing...
    python -m pip install pyinstaller
    if %ERRORLEVEL% EQU 0 (
        echo   [OK] PyInstaller installed successfully
        set /a PASS+=1
    ) else (
        echo   [FAIL] Failed to install PyInstaller
        set /a FAIL+=1
    )
)

echo.
echo ============================================
echo  Summary: !PASS! passed, !FAIL! failed
echo ============================================

if !FAIL! GTR 0 (
    echo  One or more steps failed. Review the output above.
    endlocal
    exit /b 1
)

echo  All steps completed successfully.

endlocal
exit /b 0