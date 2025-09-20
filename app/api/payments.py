import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from datetime import date, datetime

from ..database import get_db_connection
from ..auth.dependencies import get_current_user
from ..sql.payments import (
    CREATE_PAYMENT,
    GET_PENDING_PAYMENTS_BY_REALM,
    APPROVE_PAYMENT,
    GET_PAYMENTS_BY_TENANT
)

router = APIRouter(prefix="/payments", tags=["payments"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Endpoint for renters to upload proof of payment
@router.post("/upload")
async def upload_payment_proof(
    file: UploadFile = File(...),
    contract_id: int = Form(...),
    amount: float = Form(...),
    payment_date: date = Form(...),
    notes: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    username = current_user.get("username")
    if current_user.get("role") != "boarding_tenants" or not realm:
        raise HTTPException(status_code=403, detail="Only tenants of a realm can upload payments.")

    # Secure filename and define path
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{username}_{file.filename}".replace(" ", "_")
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    async with get_db_connection() as conn:
        payment_number = f"PAY-{timestamp}-{contract_id}"
        payment_id = await conn.fetchval(
            CREATE_PAYMENT,
            realm,
            contract_id,
            payment_number,
            amount,
            payment_date,
            "Bank Transfer", # Assuming method for now
            notes,
            username,
            file_path
        )
        return {"id": payment_id, "message": "Payment proof uploaded successfully. Awaiting approval."}

# Endpoint for managers to approve a payment
@router.post("/{payment_id}/approve")
async def approve_payment(
    payment_id: int,
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if current_user.get("role") != "boarding_managers" or not realm:
        raise HTTPException(status_code=403, detail="Only managers of a realm can approve payments.")

    async with get_db_connection() as conn:
        res = await conn.execute(APPROVE_PAYMENT, payment_id, realm)
        if res == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Payment not found or access denied.")
        return {"message": f"Payment {payment_id} has been approved."}

# Endpoint for managers to see pending payments
@router.get("/pending")
async def get_pending_payments(
    current_user: dict = Depends(get_current_user)
):
    realm = current_user.get("realm")
    if current_user.get("role") != "boarding_managers" or not realm:
        raise HTTPException(status_code=403, detail="Only managers of a realm can view pending payments.")

    async with get_db_connection() as conn:
        payments = await conn.fetch(GET_PENDING_PAYMENTS_BY_REALM, realm)
        return [dict(payment) for payment in payments]

@router.get("/my")
async def get_my_payments(current_user: dict = Depends(get_current_user)):
    realm = current_user.get("realm")
    username = current_user.get("username")
    if not realm or not username:
        raise HTTPException(status_code=403, detail="Invalid user.")

    async with get_db_connection() as conn:
        payments = await conn.fetch(GET_PAYMENTS_BY_TENANT, username, realm)
        return [dict(payment) for payment in payments]
