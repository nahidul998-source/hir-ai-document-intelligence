import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models_phase8 import FeatureFlag, ValidationRule, SystemConfig
from app.infrastructure.repositories.admin import AdminRepository

logger = logging.getLogger(__name__)


class SystemConfigService:
    """
    Handles feature flags, validation rules, AI provider settings, dynamic prompts, and platform configurations.
    """
    def __init__(self, db: AsyncSession, repo: Optional[AdminRepository] = None):
        self.db = db
        self.repo = repo or AdminRepository(db)

    async def list_feature_flags(self) -> List[FeatureFlag]:
        return await self.repo.get_feature_flags()

    async def set_feature_flag(self, key: str, is_enabled: bool, description: Optional[str] = None) -> FeatureFlag:
        flags = await self.repo.get_feature_flags()
        existing = next((f for f in flags if f.key == key), None)
        if existing:
            existing.is_enabled = is_enabled
            if description:
                existing.description = description
            flag = existing
        else:
            flag = FeatureFlag(key=key, is_enabled=is_enabled, description=description)
            flag = await self.repo.save_feature_flag(flag)
        await self.db.commit()
        logger.info(f"Set feature flag '{key}' to {is_enabled}")
        return flag

    async def list_validation_rules(self) -> List[ValidationRule]:
        return await self.repo.get_validation_rules()

    async def save_validation_rule(
        self,
        field_name: str,
        rule_type: str,
        constraint_value: str,
        error_message: str,
        is_enabled: bool = True
    ) -> ValidationRule:
        rule = ValidationRule(
            field_name=field_name,
            rule_type=rule_type,
            constraint_value=constraint_value,
            error_message=error_message,
            is_enabled=is_enabled
        )
        saved = await self.repo.save_validation_rule(rule)
        await self.db.commit()
        return saved

    async def set_system_setting(self, key: str, value: str, category: str = "general", description: Optional[str] = None) -> SystemConfig:
        setting = await self.repo.set_system_config(key=key, value=value, category=category, description=description)
        await self.db.commit()
        return setting

    async def list_system_settings(self) -> List[SystemConfig]:
        return await self.repo.get_system_configs()
