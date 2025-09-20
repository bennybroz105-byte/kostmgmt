from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..database import get_db_connection
from ..auth.dependencies import get_current_user
from ..sql.rooms import GET_AVAILABLE_ROOMS, CREATE_ROOM, UPDATE_ROOM, DELETE_ROOM

router = APIRouter(prefix="/rooms", tags=["rooms"])

class RoomUpdate(BaseModel):
    room_number: str
    floor: Optional[str] = None
    monthly_rate: float
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    status: str

class RoomCreate(BaseModel):
    room_number: str
    floor: Optional[str] = None
    monthly_rate: float
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

@router.get("/available")
async def get_available_rooms(
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if not realm:
        raise HTTPException(status_code=400, detail="User is not associated with a realm.")

    async with get_db_connection() as conn:
        rooms = await conn.fetch(GET_AVAILABLE_ROOMS, realm)
        return [dict(room) for room in rooms]

@router.post("/")
async def create_room(
    room: RoomCreate,
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if current_user.get("role") != "boarding_managers" or not realm:
        raise HTTPException(
            status_code=403,
            detail="Only managers of a realm can create rooms."
        )

    async with get_db_connection() as conn:
        try:
            room_id = await conn.fetchval(
                CREATE_ROOM,
                realm,
                room.room_number,
                room.floor,
                room.monthly_rate,
                room.description,
                room.attributes
            )
            return {"id": room_id, "message": "Room created successfully."}
        except Exception as e:
            # This could be a unique constraint violation
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/{room_id}")
async def update_room(
    room_id: int,
    room: RoomUpdate,
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if current_user.get("role") != "boarding_managers" or not realm:
        raise HTTPException(
            status_code=403,
            detail="Only managers of a realm can update rooms."
        )

    async with get_db_connection() as conn:
        # Ensure the room exists and belongs to the manager's realm before updating
        res = await conn.execute(
            UPDATE_ROOM,
            room.room_number,
            room.floor,
            room.monthly_rate,
            room.description,
            room.attributes,
            room.status,
            room_id,
            realm
        )
        if res == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Room not found or access denied.")
        return {"message": "Room updated successfully."}

@router.delete("/{room_id}")
async def delete_room(
    room_id: int,
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if current_user.get("role") != "boarding_managers" or not realm:
        raise HTTPException(
            status_code=403,
            detail="Only managers of a realm can delete rooms."
        )

    async with get_db_connection() as conn:
        # Prevent deletion of occupied rooms
        status = await conn.fetchval("SELECT status FROM rooms WHERE id = $1 AND realm = $2", room_id, realm)
        if status is None:
            raise HTTPException(status_code=404, detail="Room not found or access denied.")
        if status == 'occupied':
            raise HTTPException(status_code=400, detail="Cannot delete an occupied room.")

        res = await conn.execute(DELETE_ROOM, room_id, realm)
        if res == "DELETE 0":
            raise HTTPException(status_code=404, detail="Room not found or access denied.")
        return {"message": "Room deleted successfully."}