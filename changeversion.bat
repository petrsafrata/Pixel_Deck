@echo off

if "%~1"=="" (
    echo Usage: changeversion.bat MAJOR.MINOR.PATCH
    exit /b 1
)

set "NEW_VERSION=%~1"

> "VERSION" echo %NEW_VERSION%

echo Version updated to %NEW_VERSION%.