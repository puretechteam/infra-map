@echo off
setlocal

cd /d "%~dp0"

for /f "usebackq delims=" %%v in (`type "VERSION"`) do set VERSION=%%v

echo Building infra-map version %VERSION%...

pyinstaller --noconfirm ^
    --name "infra-map-%VERSION%" ^
    --add-data "data;data" ^
    --add-data "static;static" ^
    --distpath=dist ^
    --workpath=build ^
    app.py

if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: Build completed for infra-map-%VERSION%
) else (
    echo FAILURE: Build failed for infra-map-%VERSION%
    exit /b 1
)

endlocal