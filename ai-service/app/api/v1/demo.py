from app.security.tenant import verify_tenant_access
from app.utils.django_client import DjangoInternalClient
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/demo", tags=["Tenant Demo"])


@router.get("")
def tenant_demo(data=Depends(verify_tenant_access)):
    return {
        "message": "Tenant access granted",
        "tenant_id": data["tenant_id"],
        "user_id": data["token_payload"]["user_id"],
        "role": data["token_payload"]["role"],
    }


@router.get("/django-check")
def django_internal_check():
    return DjangoInternalClient.get_internal_demo("dummy_token")
