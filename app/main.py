import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router as api_router
from app.core.db import database, init_db_tables
from app.core.settings import settings
from app.core.probes import run_probes

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("uvicorn.startup")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("Connecting to Database and Cache...")
    await database.connect()
    
    # 1. Create Tables (Prevent Race Condition with try/except)
    try:
        await init_db_tables()
    except Exception as e:
        logger.warning(f"Table init skipped (Race Condition): {e}")

    # 2. Load Settings
    logger.info("Loading System Settings...")
    await settings.load()
    
    # 3. Start Background Probes (OpenAI/FAA Health Checks)
    asyncio.create_task(run_probes())
    
    logger.info("Systems Online.")
    yield
    # SHUTDOWN
    logger.info("Disconnecting...")
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if os.path.exists("/app/static/assets"):
    app.mount("/assets", StaticFiles(directory="/app/static/assets"), name="assets")

@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
async def favicon():
    possible_paths = ["/app/static/favicon.png", "/app/static/favicon.ico"]
    for path in possible_paths:
        if os.path.exists(path):
            return FileResponse(path)
    return {"error": "Favicon not found"}

@app.get("/{full_path:path}")
async def serve_app(full_path: str):
    file_path = os.path.join("/app/static", full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    if os.path.exists("/app/static/index.html"):
        return FileResponse("/app/static/index.html")
    return {"error": "Frontend not built. Check Dockerfile."}