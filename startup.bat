@echo off
if not defined SHARED_DIR (set SHARED_DIR=d:\shared)
if not defined PROJECTS_DIR (set PROJECTS_DIR=d:\projects)

set PYTHONHOME=%SHARED_DIR%\python34
set PATH=%PYTHONHOME%;%PYTHONHOME%\Scripts;%PATH%
set PYTHONPATH=%PROJECTS_DIR%\ben10\source\python;%PYTHONPATH%

call %~dp0ii.bat reset
