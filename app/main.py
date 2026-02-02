import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from app.core.logger import init_db

init_db()

app = FastAPI()

# Allow CORS for local development (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Include API Routes
app.include_router(routes.router)

# 2. Serve Static Assets (JS/CSS built by React)
if os.path.exists("/app/static/assets"):
    app.mount("/assets", StaticFiles(directory="/app/static/assets"), name="assets")

# --- NEW: Explicit Favicon Handling ---
@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
async def favicon():
    # Tries both common names in your static folder
    possible_paths = ["/app/static/favicon.png", "/app/static/favicon.ico"]
    for path in possible_paths:
        if os.path.exists(path):
            return FileResponse(path)
    return {"error": "Favicon not found"}

# 3. Catch-All: Serve static files if they exist, otherwise index.html (SPA support)
@app.get("/{full_path:path}")
async def serve_app(full_path: str):
    # 1. Check if the specific file exists (e.g. robots.txt)
    file_path = os.path.join("/app/static", full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # 2. If not, serve index.html and let React handle the routing
    if os.path.exists("/app/static/index.html"):
        return FileResponse("/app/static/index.html")
    
    return {"error": "Frontend not built. Check Dockerfile."}