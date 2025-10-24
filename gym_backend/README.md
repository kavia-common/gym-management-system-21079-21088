# Gym Backend

FastAPI backend for the gym management application.

## Running locally (no venv activation required)

Dependencies are managed via `requirements.txt`. In the CI/preview environment, they will be installed in the container's Python environment. To run:

1. Install dependencies:
   pip3 install -r requirements.txt

2. Start the server (port 3001):
   uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

Health check:
- GET http://localhost:3001/health

WebSocket test:
- Connect to ws://localhost:3001/ws/echo
- Send a message; the server echoes it back.

Environment variables are read from the container `.env` (already provided in this repo). Do not commit secrets to version control.
