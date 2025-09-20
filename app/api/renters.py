from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..database import get_db_connection
from ..auth.dependencies import get_current_user
from ..sql.renters import CREATE_RADCHECK_USER, CREATE_RADUSERGROUP_USER

router = APIRouter(prefix="/renters", tags=["renters"])

class RenterCreate(BaseModel):
    username: str # This should be the full username@realm
    password: str

@router.post("/")
async def create_renter(
    renter: RenterCreate,
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if current_user.get("role") != "boarding_managers" or not realm:
        raise HTTPException(
            status_code=403,
            detail="Only managers of a realm can create renters."
        )

    # Basic validation
    if '@' not in renter.username or renter.username.split('@', 1)[1] != realm:
        raise HTTPException(
            status_code=400,
            detail=f"New renter username must belong to the manager's realm ('{realm}')."
        )

    async with get_db_connection() as conn:
        async with conn.transaction():
            try:
                # Create user password
                await conn.execute(CREATE_RADCHECK_USER, renter.username, renter.password)
                # Assign user to tenant group
                await conn.execute(CREATE_RADUSERGROUP_USER, renter.username)
            except Exception as e:
                # Could be a unique violation if user exists
                raise HTTPException(status_code=400, detail=f"Failed to create renter: {e}")

    return {"message": f"Renter {renter.username} created successfully."}
