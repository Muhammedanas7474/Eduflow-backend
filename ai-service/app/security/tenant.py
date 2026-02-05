from app.security.jwt import verify_jwt_token
from fastapi import Depends, HTTPException, status


def verify_tenant_access(token_payload=Depends(verify_jwt_token)):
    tenant_id = token_payload.get("tenant_id")

    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tenant not found in token"
        )

    return {
        "tenant_id": tenant_id,
        "token_payload": token_payload,
    }
