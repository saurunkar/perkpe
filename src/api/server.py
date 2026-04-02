import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.v1_routes import router as v1_router

app = FastAPI(title="Sentinel Finance OS API")

# Mount API routes
app.include_router(v1_router, prefix="/api/v1")

# Get absolute path to the static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Mount static files (at root levels)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_dashboard():
    """Serves the main dashboard HTML file."""
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/{path:path}")
async def catch_all(path: str):
    """
    Catch-all route to serve static files from the root.
    Note: In production, a proper static file server (Nginx/Cloud CDN) is preferred.
    """
    file_path = os.path.join(static_dir, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
