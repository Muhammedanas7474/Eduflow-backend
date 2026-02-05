from app.security.jwt import verify_jwt_token
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/protected")
def protected_route(token_payload: dict = Depends(verify_jwt_token)):
    return {"message": "JWT is valid", "token_payload": token_payload}
