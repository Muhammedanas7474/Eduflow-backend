from app.security.rbac import require_roles
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/courses", tags=["Courses"])


# 1️⃣ Everyone in tenant can view courses
@router.get("")
def list_courses(data=Depends(require_roles("STUDENT", "INSTRUCTOR", "ADMIN"))):
    return {
        "action": "list_courses",
        "role": data["token_payload"]["role"],
        "tenant_id": data["tenant_id"],
    }


# 2️⃣ Only INSTRUCTOR & ADMIN can create courses
@router.post("")
def create_course(data=Depends(require_roles("INSTRUCTOR", "ADMIN"))):
    return {
        "action": "create_course",
        "created_by_role": data["token_payload"]["role"],
        "tenant_id": data["tenant_id"],
    }


# 3️⃣ Only ADMIN can see all courses
@router.get("/all")
def list_all_courses(data=Depends(require_roles("ADMIN"))):
    return {
        "action": "list_all_courses",
        "visible_to": "ADMIN",
        "tenant_id": data["tenant_id"],
    }
