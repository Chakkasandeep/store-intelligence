@echo off
echo Checking if Store Intelligence API is running on port 8000...
echo.
curl -s -o nul -w "HTTP %%{http_code}\n" http://127.0.0.1:8000/health 2>nul
if errorlevel 1 (
  echo.
  echo FAILED - API is NOT running.
  echo.
  echo Start it in another window:
  echo   cd store-intelligence
  echo   venv\Scripts\activate
  echo   set PYTHONPATH=.
  echo   set EVENTS_JSONL=data\events\output.jsonl
  echo   uvicorn backend.main:app --host 127.0.0.1 --port 8000
  echo.
  echo Then run this script again.
  exit /b 1
)
echo.
echo OK - API is up. Open http://127.0.0.1:8000/docs
curl -s http://127.0.0.1:8000/health
echo.
exit /b 0
