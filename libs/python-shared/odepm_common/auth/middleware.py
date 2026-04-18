from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key")
ALGORITHM = "HS256"

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=403, detail="Could not validate credentials"
            )
        return {"user_id": user_id, "roles": payload.get("roles", [])}
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


async def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-KEY")
    if not api_key:
        raise HTTPException(status_code=403, detail="API Key missing")
    # In production, check against database/redis
    if api_key != os.getenv("ADMIN_API_KEY", "propex_admin_key"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True
