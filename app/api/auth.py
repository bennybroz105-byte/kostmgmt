from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt

from ..database import get_db_connection
from ..config import get_settings

router = APIRouter(tags=["auth"])
settings = get_settings()

async def verify_password(plain_password: str, username: str, conn) -> bool:
    # This is a simplified check. In a real scenario, you'd handle hashed passwords.
    # FreeRADIUS can use many password schemes. We assume Cleartext-Password for now.
    stored_password = await conn.fetchval(
        "SELECT value FROM radcheck WHERE username = $1 AND attribute = 'Cleartext-Password'",
        username
    )
    return stored_password is not None and stored_password == plain_password

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
