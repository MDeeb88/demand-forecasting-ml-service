@echo off
cd /d "%~dp0"

echo Starting Demand Forecasting App...

start "Docker App" cmd /k docker-compose up --build

echo Waiting for the app to start, it might take a minute...
timeout /t 60 /nobreak > nul

start "" http://127.0.0.1:8501

exit