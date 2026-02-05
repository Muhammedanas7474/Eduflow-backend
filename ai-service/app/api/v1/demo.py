from app.security.tenant import verify_tenant_access
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/demo", tags=["Tenant Demo"])


@router.get("")
def tenant_demo(data=Depends(verify_tenant_access)):
    return {
        "message": "Tenant access granted",
        "tenant_id": data["tenant_id"],
        "user_id": data["user_id"],
        "role": data["role"],
    }
