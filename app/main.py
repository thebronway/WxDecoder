import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes

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

# 3. Catch-All: Serve React's index.html for any other route
@app.get("/{full_path:path}")
async def serve_app(full_path: str):
    if os.path.exists("/app/static/index.html"):
        return FileResponse("/app/static/index.html")
    return {"error": "Frontend not built. Check Dockerfile."}