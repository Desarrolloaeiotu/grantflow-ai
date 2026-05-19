@echo off
REM Script para iniciar FastAPI backend en segundo plano

title GrantFlow AI - FastAPI Backend

cd /d "c:\Users\Luis Mendez\OneDrive - Fundación Carulla - Aeiotu\Escritorio\Grantflow app\backend"

echo Iniciando FastAPI backend en localhost:8000...
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
