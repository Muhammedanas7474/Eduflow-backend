from app.security.tenant import verify_tenant_access
from fastapi import Depends, HTTPException, status


def require_roles(*allowed_roles: str):
    def checker(data=Depends(verify_tenant_access)):
        role = data["token_payload"]["role"]

        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Role not allowed"
            )

        return data

    return checker
