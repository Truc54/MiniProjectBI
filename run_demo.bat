@echo off
title F1 BI - Phase 2 Demo Runner (Windows)
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_demo_windows.ps1"
pause
