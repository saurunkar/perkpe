import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.v1_routes import router as v1_router
from src.api.setup_routes import router as setup_router
from src.api.product_routes import router as product_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and resources on startup."""
    from src.data.local_db import init_db
    await init_db()
    print("✅ Sentinel Finance OS started.")
    yield
    print("Sentinel Finance OS shutting down.")


app = FastAPI(title="Sentinel Finance OS API", lifespan=lifespan)

# Mount routers
app.include_router(v1_router, prefix="/api/v1")
app.include_router(setup_router, prefix="/api/setup")
app.include_router(product_router, prefix="/api/product")

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def serve_dashboard():
    """Serves the main dashboard HTML file."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all to serve static files or fall back to index.html."""
    file_path = os.path.join(static_dir, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
