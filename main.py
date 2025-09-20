from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg
from datetime import datetime
import jwt
import os
from typing import Optional, List, Dict
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Boarding House Management System")

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # Change in production

# Database connection pool
async def init_db():
    return await asyncpg.create_pool(
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        database=os.getenv("DB_NAME", "radius"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        min_size=5,
        max_size=20
    )

# Serve Next.js static files and handle client-side routing
app.mount("/static", StaticFiles(directory="frontend/out/static"), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Serve the Next.js index.html for all paths (client-side routing)
    if not full_path.startswith("api/"):
        return FileResponse("frontend/out/index.html")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Database dependency
async def get_db():
    pool = app.state.pool
    async with pool.acquire() as conn:
        yield conn

# Room endpoints
@app.get("/api/rooms/available")
async def get_available_rooms(
    conn = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        query = """
            SELECT r.*, 
                   COALESCE(json_agg(
                       json_build_object(
                           'attribute', r.attributes->>'name',
                           'value', r.attributes->>'value'
                       )
                   ) FILTER (WHERE r.attributes IS NOT NULL), '[]') as room_attributes
            FROM rooms r
            WHERE r.status = 'available'
            GROUP BY r.id
            ORDER BY r.room_number;
        """
        rooms = await conn.fetch(query)
        return [dict(room) for room in rooms]
    except Exception as e:
        logger.error(f"Error fetching available rooms: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

# Contract endpoints
@app.post("/api/contracts")
async def create_contract(
    contract_data: dict,
    conn = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with conn.transaction():
        try:
            # Verify user is a manager
            is_manager = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM radusergroup 
                    WHERE username = $1 AND groupname = 'boarding_managers'
                )
            """, current_user['sub'])

            if not is_manager:
                raise HTTPException(status_code=403, detail="Only managers can create contracts")

            # Create contract
            contract_id = await conn.fetchval("""
                INSERT INTO contracts (
                    contract_number, room_id, tenant_username, 
                    start_date, end_date, monthly_rate, deposit_amount
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, 
                contract_data['contract_number'],
                contract_data['room_id'],
                contract_data['tenant_username'],
                contract_data['start_date'],
                contract_data['end_date'],
                contract_data['monthly_rate'],
                contract_data['deposit_amount']
            )

            # Update room status
            await conn.execute("""
                UPDATE rooms SET status = 'occupied' WHERE id = $1
            """, contract_data['room_id'])

            return {"id": contract_id, "message": "Contract created successfully"}
    
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Contract number already exists")
        except Exception as e:
            logger.error(f"Error creating contract: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error")

# Receipt endpoints
@app.get("/api/contracts/{contract_id}/receipt")
async def get_contract_receipt(
    contract_id: int,
    conn = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Fetch contract and payment details
        receipt_data = await conn.fetchrow("""
            SELECT 
                c.contract_number,
                c.monthly_rate,
                r.room_number,
                p.payment_number,
                p.amount,
                p.payment_date,
                p.payment_method,
                t.username as tenant_name
            FROM contracts c
            JOIN rooms r ON c.room_id = r.id
            JOIN payments p ON p.contract_id = c.id
            JOIN radusergroup t ON c.tenant_username = t.username
            WHERE c.id = $1
            ORDER BY p.payment_date DESC
            LIMIT 1
        """, contract_id)

        if not receipt_data:
            raise HTTPException(status_code=404, detail="Receipt not found")

        # Convert to dict and format dates
        receipt = dict(receipt_data)
        receipt['payment_date'] = receipt['payment_date'].strftime('%Y-%m-%d')
        
        return receipt

    except Exception as e:
        logger.error(f"Error fetching receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

# Startup event to initialize database pool
@app.on_event("startup")
async def startup_event():
    app.state.pool = await init_db()

# Shutdown event to close database pool
@app.on_event("shutdown")
async def shutdown_event():
    await app.state.pool.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4
    )