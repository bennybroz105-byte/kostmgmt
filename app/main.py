from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .api import rooms, contracts, payments, renters, auth
from .database import get_db_pool
import os

app = FastAPI(title="Boarding House Management API")

# --- Static files serving ---
STATIC_DIR = "frontend/out"

# Mount the Next.js static assets directory
app.mount(
    "/_next",
    StaticFiles(directory=os.path.join(STATIC_DIR, "_next")),
    name="next-static"
)

# Include routers
app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(contracts.router)
app.include_router(payments.router)
app.include_router(renters.router)

@app.on_event("startup")
async def startup():
    app.state.pool = await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

# Catch-all to serve the Next.js app's index.html
@app.get("/{full_path:path}")
async def serve_next_app(full_path: str):
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    # This is useful for development, when the frontend hasn't been built yet
    return {"message": "API is running. Frontend has not been built yet."}