from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..config import get_settings
from ..database import get_db_connection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
settings = get_settings()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    async with get_db_connection() as conn:
        # Check user exists and get their role from radusergroup
        user = await conn.fetchrow("""
            SELECT 
                u.username,
                u.groupname as role
            FROM radusergroup u
            WHERE u.username = $1
        """, username)
        
        if user is None:
            raise credentials_exception
            
        return dict(user)