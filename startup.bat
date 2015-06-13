@echo off
if not defined SHARED_DIR (set SHARED_DIR=d:\Shared)
if not defined PROJECTS_DIR (set PROJECTS_DIR=x:)

set PYTHONHOME=%SHARED_DIR%\python27
set PATH=%PYTHONHOME%;%PYTHONHOME%\Scripts;%PATH%
set PYTHONPATH=%PROJECTS_DIR%\ben10\source\python;%PYTHONPATH%

call %~dp0ii.bat reset
