from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict

# PUBLIC_INTERFACE
def create_app() -> FastAPI:
    """Create and configure the FastAPI application for the Gym Backend.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Gym Management Backend API",
        description=(
            "Backend API for the gym management application. "
            "Provides endpoints for authentication, membership, schedules, trainers, and admin operations."
        ),
        version="0.1.0",
        openapi_tags=[
            {"name": "health", "description": "Health and status checks"},
            {"name": "websocket", "description": "Real-time websocket endpoints and usage"},
        ],
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class HealthResponse(BaseModel):
        status: str = Field(..., description="Status string indicating service health, e.g. 'ok'")
        service: str = Field(..., description="Name of the service")
        version: str = Field(..., description="Version of the service")
        details: Dict[str, Any] | None = Field(default=None, description="Optional extra diagnostic details")

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
        summary="Service health check",
        description="Returns the current health of the Gym Backend service. Useful for readiness and liveness probes.",
        responses={200: {"description": "Service is healthy"}},
    )
    # PUBLIC_INTERFACE
    def health() -> HealthResponse:
        """Health endpoint returning service status."""
        return HealthResponse(status="ok", service="gym-backend", version="0.1.0")

    # WebSocket usage help route for API docs visibility
    @app.get(
        "/docs/websocket",
        tags=["websocket"],
        summary="WebSocket usage help",
        description=(
            "Usage notes for WebSocket connections.\n\n"
            "- Connect to ws://<host>:3001/ws/echo\n"
            "- Send a message and the server will echo it back prefixed with 'echo: '\n"
        ),
        responses={200: {"description": "WebSocket usage information returned as text"}},
    )
    # PUBLIC_INTERFACE
    def websocket_usage() -> Dict[str, str]:
        """Return basic WebSocket usage instructions for clients."""
        return {
            "note": "Use ws://<host>:3001/ws/echo to test a simple echo WebSocket.",
            "example": "After connecting, send any text and receive 'echo: <text>' back.",
        }

    @app.websocket(
        "/ws/echo"
    )
    # PUBLIC_INTERFACE
    async def ws_echo(websocket: WebSocket):
        """A simple echo WebSocket endpoint.

        OperationId: websocket_echo
        Summary: Echo WebSocket endpoint
        Description: Connect and exchange messages; the server echoes each message back.

        Connection:
        - URL: ws://<host>:3001/ws/echo
        - Protocols: text frames
        """
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"echo: {data}")
        except Exception:
            # Client disconnected or error occurred; just close.
            try:
                await websocket.close()
            except Exception:
                pass

    return app


# PUBLIC_INTERFACE
# Entrypoint used by uvicorn: src.api.main:app
app = create_app()
