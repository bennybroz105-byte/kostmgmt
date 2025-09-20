from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt

from ..database import get_db_connection
from ..config import get_settings

router = APIRouter(tags=["auth"])
settings = get_settings()

import hashlib

async def verify_password(plain_password: str, username: str, conn) -> bool:
    stored_password_record = await conn.fetchrow(
        "SELECT value, attribute FROM radcheck WHERE username = $1 AND (attribute = 'Cleartext-Password' OR attribute = 'Password-With-Header')",
        username
    )

    if not stored_password_record:
        return False

    stored_value = stored_password_record['value']
    attribute = stored_password_record['attribute']

    if attribute == 'Cleartext-Password':
        return stored_value == plain_password

    if attribute == 'Password-With-Header':
        if not stored_value.startswith('{crypt-sha256}'):
            # Unsupported hash format
            return False

        stored_hash = stored_value.replace('{crypt-sha256}', '')

        # Hash the provided plain password with SHA-256
        h = hashlib.sha256()
        h.update(plain_password.encode('utf-8'))
        provided_hash = h.hexdigest()

        return provided_hash == stored_hash

    return False

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    async with get_db_connection() as conn:
        user_is_valid = await verify_password(form_data.password, form_data.username, conn)
        if not user_is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Fetch user role to include in token
        user_role = await conn.fetchval(
            "SELECT groupname FROM radusergroup WHERE username = $1",
            form_data.username
        )
        if not user_role:
            raise HTTPException(status_code=400, detail="User is not assigned to a group.")

    # Parse realm
    realm = form_data.username.split('@', 1)[1] if '@' in form_data.username else None

    token_data = {
        "sub": form_data.username,
        "role": user_role,
        "realm": realm
    }

    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}
