@echo off
REM Build script to compile program, copy folders, create archive, and clean up

REM Step 1: Compile main.py to single executable without console
pyinstaller --onefile --noconsole main.py

REM Step 2: Prepare build output folder
if exist build_output (
    rmdir /s /q build_output
)
mkdir "PvZ Modding Tool"

REM Step 3: Copy executable to build_output
copy dist\main.exe "PvZ Modding Tool\"

REM Step 4: Copy example folder fully
xcopy /E /I /Y example "PvZ Modding Tool\example"

REM Step 5: Create empty projects folder inside build_output
mkdir "PvZ Modding Tool\projects"

REM Step 6: Copy tools folder fully
xcopy /E /I /Y tools "PvZ Modding Tool\tools"

REM Step 7: Create zip archive of build_output folder
REM Using powershell Compress-Archive
powershell -Command "Compress-Archive -Path 'PvZ Modding Tool\*' -DestinationPath PvZ_Modding_Tool.zip -Force"

REM Step 8: Clean up .spec files and pyinstaller leftovers
del /Q *.spec
rmdir /S /Q build
rmdir /S /Q dist
rmdir /S /Q __pycache__

echo Build complete.
