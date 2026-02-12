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
from src.config import HOST, PORT, GOOGLE_API_KEY

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

# Add CORS middleware for security
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """Health check endpoint with API key validation."""
    api_key_configured = bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "your_api_key_here")
    return {
        "status": "ok",
        "version": "1.0.0",
        "api_key_configured": api_key_configured,
        "ready": api_key_configured
    }


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
        # Check API key first
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_api_key_here":
            await websocket.send_json({
                "event_type": "error",
                "message": "Google API key not configured. Please set GOOGLE_API_KEY in your .env file."
            })
            await websocket.close()
            return
        
        # Wait for the research query
        raw = await websocket.receive_text()
        
        # Validate JSON payload
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await websocket.send_json({
                "event_type": "error",
                "message": "Invalid JSON format in request"
            })
            await websocket.close()
            return
        
        query = payload.get("query", "").strip()

        # Validate query
        if not query:
            await websocket.send_json({"event_type": "error", "message": "No query provided"})
            await websocket.close()
            return
        
        if len(query) < 5:
            await websocket.send_json({"event_type": "error", "message": "Query too short. Please provide a more detailed question."})
            await websocket.close()
            return
        
        if len(query) > 500:
            await websocket.send_json({"event_type": "error", "message": "Query too long. Please keep it under 500 characters."})
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
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        try:
            await websocket.send_json({"event_type": "error", "message": "Invalid JSON in research results"})
        except Exception:
            pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        error_msg = str(e)
        
        # Provide user-friendly error messages
        if "api key" in error_msg.lower() or "invalid" in error_msg.lower():
            user_msg = "API key error. Please check your Google API key configuration."
        elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
            user_msg = "Rate limit exceeded. Please wait a moment and try again."
        elif "timeout" in error_msg.lower():
            user_msg = "Request timed out. The query might be too complex. Try simplifying it."
        else:
            user_msg = f"An error occurred during research: {error_msg}"
        
        try:
            await websocket.send_json({"event_type": "error", "message": user_msg})
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
