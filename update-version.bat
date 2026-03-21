@echo off

if "%~1"=="" (
    echo Usage: update-version.bat ^<MAJOR.MINOR.PATCH^>
    echo Example: update-version.bat 1.1.0
    exit /b 1
)

set "NEW_VERSION=%~1"

echo.
echo ===============================
echo Updating version to %NEW_VERSION%
echo ===============================

:: 1) Update VERSION file (only this file)
> "VERSION" echo %NEW_VERSION%
echo VERSION updated.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo Not a git repository, skipping commit.
  echo Done.
  exit /b 0
)

git add VERSION
git commit -m "VERSION: %NEW_VERSION%"

if errorlevel 1 (
  echo Git commit failed.
  exit /b 1
)

echo Version committed.
echo.
echo =====================================
echo Version update complete.
echo Push to trigger CI/CD:
echo git push
echo =====================================