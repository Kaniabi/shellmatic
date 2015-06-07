@echo off
set SHELLMATIC_EXE=python "%~dp0_ii.py"
set SHELLMATIC_BATCH=%TEMP%\.shellmatic.bat
%SHELLMATIC_EXE% %*

@if exist "%SHELLMATIC_BATCH%" (
    type "%SHELLMATIC_BATCH%"
    del /q "%SHELLMATIC_BATCH%"
)