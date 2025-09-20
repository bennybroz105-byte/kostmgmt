from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .api import rooms, contracts, payments
from .database import get_db_pool

app = FastAPI(title="Boarding House Management API")

# Mount static files directory for Next.js frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(rooms.router)
app.include_router(contracts.router)
app.include_router(payments.router)

@app.on_event("startup")
async def startup():
    app.state.pool = await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()