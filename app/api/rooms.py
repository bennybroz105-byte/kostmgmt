from fastapi import APIRouter, Depends, HTTPException
from ..database import get_db_connection
from ..auth.dependencies import get_current_user
from ..sql.rooms import GET_AVAILABLE_ROOMS

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.get("/available")
async def get_available_rooms(
    current_user: dict = Depends(get_current_user)
):
    async with get_db_connection() as conn:
        rooms = await conn.fetch(GET_AVAILABLE_ROOMS)
        return [dict(room) for room in rooms]