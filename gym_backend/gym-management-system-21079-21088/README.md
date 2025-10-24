# gym-management-system-21079-21088

A fullstack gym management application.

## Backend (gym_backend) quick start

- Change directory:
  - cd gym_backend

- Install dependencies (no venv activation required):
  - pip3 install -r requirements.txt

- Start server on port 3001:
  - bash start.sh
  - or
  - uvicorn src.api.main:app --host 0.0.0.0 --port 3001

Health check:
- GET http://localhost:3001/health

WebSocket:
- ws://localhost:3001/ws/echo

Notes:
- The start script and instructions do not activate a virtual environment. Dependencies are installed directly into the container's Python environment.
- Ensure the container exposes port 3001.
