"""
FastAPI server — serves the web UI and provides API + WebSocket endpoints.
"""
import asyncio
import json
import logging
import os
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dataclasses import asdict

from src.agent import ResearchAgent, ResearchEvent
from src.config import HOST, PORT

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title="Deep Research Agent",
    description="AI-powered multi-source research agent",
    version="1.0.0",
)

# Serve static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Ensure reports directory exists
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


# ── Routes ────────────────────────────────────────────────
@app.get("/")
async def index():
    """Serve the landing page."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/research")
async def research_page():
    """Serve the research page."""
    return FileResponse(os.path.join(STATIC_DIR, "research.html"))


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


# ── WebSocket Research Endpoint ───────────────────────────
@app.websocket("/ws/research")
async def websocket_research(websocket: WebSocket):
    """
    WebSocket endpoint for real-time research.

    Client sends: {"query": "research question here"}
    Server streams: {"event_type": "...", "message": "...", "data": {...}}
    """
    await websocket.accept()
    logger.info("WebSocket connected")

    try:
        # Wait for the research query
        raw = await websocket.receive_text()
        payload = json.loads(raw)
        query = payload.get("query", "").strip()

        if not query:
            await websocket.send_json({"event_type": "error", "message": "No query provided"})
            await websocket.close()
            return

        logger.info(f"Research request: '{query}'")

        # Create agent and event handler
        agent = ResearchAgent()

        async def on_event(event: ResearchEvent):
            """Send research events to the WebSocket client."""
            try:
                await websocket.send_json({
                    "event_type": event.event_type,
                    "message": event.message,
                    "data": event.data,
                    "timestamp": event.timestamp,
                })
            except Exception:
                pass

        # Run research
        report = await agent.research(query=query, on_event=on_event)

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c if c.isalnum() or c == ' ' else '' for c in query)[:50].strip().replace(' ', '_')
        filename = f"{timestamp}_{safe_query}.md"
        filepath = os.path.join(REPORTS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report.report_markdown)

        # Send final report
        await websocket.send_json({
            "event_type": "report",
            "message": "Final report ready",
            "data": {
                "markdown": report.report_markdown,
                "total_sources": len(report.sources),
                "iterations": report.iterations,
                "contradictions": len(report.contradictions),
                "sources": report.sources[:50],  # Limit to avoid huge payload
                "filename": filename,
            },
        })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"event_type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
