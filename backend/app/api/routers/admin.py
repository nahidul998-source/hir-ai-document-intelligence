import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.api.deps import get_current_user
from app.infrastructure.database.models import User
from app.api.security.rbac import RequirePermission, Permissions

from app.application.services.admin.user_tenant_service import UserTenantService
from app.application.services.admin.system_config_service import SystemConfigService
from app.application.services.admin.ops_management_service import OpsManagementService

router = APIRouter(tags=["Enterprise Administration"])

class CreateRoleRequest(BaseModel):
    name: str
    permissions: Dict[str, Any] = {}

class CreateTenantRequest(BaseModel):
    name: str
    code: str
    max_users: int = 50
    storage_quota_gb: float = 100.0
    settings: Optional[Dict[str, Any]] = None

class FeatureFlagRequest(BaseModel):
    key: str
    is_enabled: bool
    description: Optional[str] = None

class ValidationRuleRequest(BaseModel):
    field_name: str
    rule_type: str
    constraint_value: str
    error_message: str
    is_enabled: bool = True

class SystemConfigRequest(BaseModel):
    key: str
    value: Any
    category: str = "general"
    description: Optional[str] = None

class ApiKeyRequest(BaseModel):
    name: str
    scopes: Optional[List[str]] = None
    expire_days: int = 90


# User & Tenant Management
@router.get("/users", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_READ))])
async def list_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists platform users for admin management."""
    service = UserTenantService(db)
    users = await service.list_users(skip=skip, limit=limit)
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "is_active": u.is_active,
            "role_id": str(u.role_id),
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@router.get("/roles", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_READ))])
async def list_admin_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists defined RBAC roles and permission maps."""
    service = UserTenantService(db)
    roles = await service.list_roles()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "permissions": r.permissions
        }
        for r in roles
    ]


@router.post("/roles", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def create_admin_role(
    payload: CreateRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new RBAC role."""
    service = UserTenantService(db)
    role = await service.create_role(name=payload.name, permissions=payload.permissions)
    return {"id": str(role.id), "name": role.name}


@router.get("/tenants", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_READ))])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists multi-tenant organizations and quotas."""
    service = UserTenantService(db)
    tenants = await service.list_tenants(skip=skip, limit=limit)
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "code": t.code,
            "status": t.status,
            "max_users": t.max_users,
            "storage_quota_gb": t.storage_quota_gb
        }
        for t in tenants
    ]


@router.post("/tenants", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def create_tenant(
    payload: CreateTenantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registers a new multi-tenant organization."""
    service = UserTenantService(db)
    tenant = await service.create_tenant(
        name=payload.name,
        code=payload.code,
        max_users=payload.max_users,
        storage_quota_gb=payload.storage_quota_gb,
        settings=payload.settings
    )
    return {"id": str(tenant.id), "name": tenant.name, "code": tenant.code}


# Feature Flags & System Configs
@router.get("/feature-flags", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_READ))])
async def list_feature_flags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists dynamic feature flags."""
    service = SystemConfigService(db)
    flags = await service.list_feature_flags()
    return [
        {
            "id": str(f.id),
            "key": f.key,
            "description": f.description,
            "is_enabled": f.is_enabled
        }
        for f in flags
    ]


@router.post("/feature-flags", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def set_feature_flag(
    payload: FeatureFlagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggles or creates a dynamic feature flag."""
    service = SystemConfigService(db)
    flag = await service.set_feature_flag(
        key=payload.key,
        is_enabled=payload.is_enabled,
        description=payload.description
    )
    return {"id": str(flag.id), "key": flag.key, "is_enabled": flag.is_enabled}


@router.get("/validation-rules", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_READ))])
async def list_validation_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists field validation rules."""
    service = SystemConfigService(db)
    rules = await service.list_validation_rules()
    return [
        {
            "id": str(r.id),
            "field_name": r.field_name,
            "rule_type": r.rule_type,
            "constraint_value": r.constraint_value,
            "error_message": r.error_message,
            "is_enabled": r.is_enabled
        }
        for r in rules
    ]


@router.post("/validation-rules", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def save_validation_rule(
    payload: ValidationRuleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Saves a custom field extraction validation rule."""
    service = SystemConfigService(db)
    rule = await service.save_validation_rule(
        field_name=payload.field_name,
        rule_type=payload.rule_type,
        constraint_value=payload.constraint_value,
        error_message=payload.error_message,
        is_enabled=payload.is_enabled
    )
    return {"id": str(rule.id), "field_name": rule.field_name}


@router.get("/system-config", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_READ))])
async def list_system_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists global system configurations."""
    service = SystemConfigService(db)
    configs = await service.list_system_settings()
    return [
        {
            "id": str(c.id),
            "key": c.key,
            "value": c.value,
            "category": c.category,
            "description": c.description
        }
        for c in configs
    ]


@router.post("/system-config", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def set_system_config(
    payload: SystemConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sets a global system configuration setting."""
    service = SystemConfigService(db)
    config = await service.set_system_setting(
        key=payload.key,
        value=str(payload.value),
        category=payload.category,
        description=payload.description
    )
    return {"id": str(config.id), "key": config.key, "value": config.value}


# Operations, API Keys, Queues, Backups
@router.get("/api-keys", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_READ))])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists generated integration API keys."""
    ops = OpsManagementService(db)
    keys = await ops.list_api_keys()
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "scopes": k.scopes,
            "is_active": k.is_active,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None
        }
        for k in keys
    ]


@router.post("/api-keys", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def create_api_key(
    payload: ApiKeyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a new external integration API Key."""
    ops = OpsManagementService(db)
    return await ops.create_api_key(
        name=payload.name,
        user_id=current_user.id,
        scopes=payload.scopes,
        expire_days=payload.expire_days
    )


@router.delete("/api-keys/{key_id}", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def revoke_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revokes an active integration API key."""
    ops = OpsManagementService(db)
    await ops.revoke_api_key(key_id)
    return {"status": "revoked", "id": str(key_id)}


@router.post("/queues/{queue_name}/purge", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def purge_queue(
    queue_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Purges all pending messages from a specified RabbitMQ queue."""
    ops = OpsManagementService(db)
    return await ops.purge_queue(queue_name)


@router.post("/backups/trigger", tags=["Enterprise Administration"], dependencies=[Depends(RequirePermission(Permissions.ADMIN_WRITE))])
async def trigger_backup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers an on-demand database & MinIO backup snapshot."""
    ops = OpsManagementService(db)
    return await ops.trigger_backup()
