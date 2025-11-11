@echo off
REM filepath: c:\Users\Royal\Desktop\CS2340\group-project\2340CourseProject\check_matches_loop.bat

echo ============================================
echo Auto-checking for new matches every 20 seconds
echo Press Ctrl+C to stop
echo ============================================
echo.

:loop
echo [%date% %time%] Checking for new matches...
python manage.py check_new_matches
echo.
echo Waiting 20 seconds...
timeout /t 20 /nobreak >nul
goto loop