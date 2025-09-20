from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import date
from ..database import get_db_connection
from ..auth.dependencies import get_current_user
from ..sql.contracts import (
    CREATE_CONTRACT,
    GET_CONTRACT_WITH_PAYMENTS,
    GET_ALL_CONTRACTS_BY_REALM,
    GET_ACTIVE_CONTRACT_BY_TENANT
)

router = APIRouter(prefix="/contracts", tags=["contracts"])

class ContractCreate(BaseModel):
    room_id: int
    tenant_username: str
    start_date: date
    end_date: date
    monthly_rate: float
    deposit_amount: float

@router.post("/")
async def create_contract(
    contract: ContractCreate,
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if current_user.get("role") != "boarding_managers" or not realm:
        raise HTTPException(
            status_code=403,
            detail="Only managers of a realm can create contracts."
        )
        
    async with get_db_connection() as conn:
        # Generate contract number (you might want to implement a better system)
        contract_number = f"CONT-{date.today().strftime('%Y%m%d')}-{contract.room_id}"
        
        contract_id = await conn.fetchval(
            CREATE_CONTRACT,
            realm,
            contract_number,
            contract.room_id,
            contract.tenant_username,
            contract.start_date,
            contract.end_date,
            contract.monthly_rate,
            contract.deposit_amount
        )
        
        # Update room status to occupied
        await conn.execute("""
            UPDATE rooms 
            SET status = 'occupied' 
            WHERE id = $1
        """, contract.room_id)
        
        return {"id": contract_id, "contract_number": contract_number}

@router.get("/{contract_id}")
async def get_contract(
    contract_id: int,
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if not realm:
        raise HTTPException(status_code=403, detail="User not associated with a realm.")

    async with get_db_connection() as conn:
        contract = await conn.fetchrow(GET_CONTRACT_WITH_PAYMENTS, contract_id, realm)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
            
        # Check if user has access (is manager or the tenant)
        if (current_user["role"] != "boarding_managers" and 
            current_user["username"] != contract["tenant_username"]):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Here you would generate the receipt (HTML or PDF)
        # For now, just return the contract data
        return dict(contract)

@router.get("/")
async def get_all_contracts(current_user: dict = Depends(get_current_user)):
    realm = current_user.get("realm")
    if current_user.get("role") != "boarding_managers" or not realm:
        raise HTTPException(
            status_code=403,
            detail="Only managers of a realm can view all contracts."
        )

    async with get_db_connection() as conn:
        contracts = await conn.fetch(GET_ALL_CONTRACTS_BY_REALM, realm)
        return [dict(contract) for contract in contracts]

@router.get("/my/active")
async def get_my_active_contract(current_user: dict = Depends(get_current_user)):
    realm = current_user.get("realm")
    username = current_user.get("username")

    if not realm or not username:
        raise HTTPException(status_code=403, detail="Invalid user.")

    async with get_db_connection() as conn:
        contract = await conn.fetchrow(GET_ACTIVE_CONTRACT_BY_TENANT, username, realm)
        if not contract:
            raise HTTPException(status_code=404, detail="No active contract found.")
        return dict(contract)