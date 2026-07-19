from fastapi import Depends, HTTPException, status
from typing import List, Callable
from app.infrastructure.database.models import User
from app.api.deps import get_current_user

# Predefined Permissions
class Permissions:
    DOCUMENT_READ = "document:read"
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_DELETE = "document:delete"
    REVIEW_READ = "review:read"
    REVIEW_WRITE = "review:write"
    REVIEW_APPROVE = "review:approve"
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    ERP_PUSH = "erp:push"
    AI_PROCESS = "ai:process"
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"

# Pre-seeded role-to-permissions mapping (typically stored in DB)
DEFAULT_ROLES = {
    "Admin": [
        Permissions.DOCUMENT_READ, Permissions.DOCUMENT_CREATE, Permissions.DOCUMENT_DELETE,
        Permissions.REVIEW_READ, Permissions.REVIEW_WRITE, Permissions.REVIEW_APPROVE,
        Permissions.PROJECT_CREATE, Permissions.PROJECT_READ, Permissions.ERP_PUSH,
        Permissions.AI_PROCESS, Permissions.ADMIN_READ, Permissions.ADMIN_WRITE
    ],
    "Merchandiser": [
        Permissions.DOCUMENT_READ, Permissions.DOCUMENT_CREATE,
        Permissions.REVIEW_READ, Permissions.REVIEW_WRITE, Permissions.REVIEW_APPROVE,
        Permissions.PROJECT_READ, Permissions.ERP_PUSH
    ],
    "Reviewer": [
        Permissions.DOCUMENT_READ, Permissions.REVIEW_READ, Permissions.REVIEW_WRITE,
        Permissions.PROJECT_READ
    ],
    "AI Worker": [
        Permissions.DOCUMENT_READ, Permissions.AI_PROCESS, Permissions.REVIEW_WRITE
    ],
    "ERP Worker": [
        Permissions.ERP_PUSH, Permissions.DOCUMENT_READ
    ],
    "Read Only": [
        Permissions.DOCUMENT_READ, Permissions.PROJECT_READ, Permissions.REVIEW_READ
    ]
}

def RequirePermission(required_permission: str) -> Callable:
    """Dependency to check if the current user has a specific permission."""
    async def permission_checker(current_user: User = Depends(get_current_user)):
        # If user.role doesn't have permissions directly cached, we lookup based on role name for now
        # In a fully DB-driven setup, this would query the role's permissions JSON.
        user_permissions = current_user.role.permissions if current_user.role and current_user.role.permissions else []
        
        # Fallback to predefined roles if DB is empty
        if not user_permissions and current_user.role and current_user.role.name in DEFAULT_ROLES:
            user_permissions = DEFAULT_ROLES[current_user.role.name]

        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {required_permission}"
            )
        return current_user
    return permission_checker
