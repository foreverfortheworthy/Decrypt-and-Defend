@echo off
setlocal enabledelayedexpansion

REM Path to Users directory
set "USER_DIR=C:\Users"

REM Target filename
set "TARGET_FILE=main_pygame.py"

REM Loop through each directory in C:\Users
for /D %%U in ("%USER_DIR%\*") do (
    REM Check if it's a valid user folder by checking for common user files (like NTUSER.DAT)
    if exist "%%U\NTUSER.DAT" (
        echo Searching in: %%U

        REM Search for the file in user's directory
        for /f "delims=" %%F in ('dir /b /s /a:-d "%%U\%TARGET_FILE%" 2^>nul') do (
            echo Found: %%F

            REM Run the Python script
            echo Running: %%F
            python "%%F"

            REM Exit after running the first found file
            goto :EOF
        )
    )
)

echo File not found in any user directory.
exit /b