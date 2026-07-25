from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.infrastructure.database.models import AIProviderConfig, AIProviderRoutingRule

class AIProviderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_configs(self) -> List[AIProviderConfig]:
        result = await self.db.execute(select(AIProviderConfig).order_by(AIProviderConfig.priority_index.asc()))
        return list(result.scalars().all())

    async def get_config_by_key(self, key: str) -> Optional[AIProviderConfig]:
        result = await self.db.execute(select(AIProviderConfig).where(AIProviderConfig.key == key))
        return result.scalar_one_or_none()

    async def update_priority(self, key: str, idx: int):
        await self.db.execute(
            update(AIProviderConfig)
            .where(AIProviderConfig.key == key)
            .values(priority_index=idx)
        )

    async def get_all_routing_rules(self) -> List[AIProviderRoutingRule]:
        result = await self.db.execute(select(AIProviderRoutingRule))
        return list(result.scalars().all())

    async def get_routing_rule_by_doc_type(self, document_type: str) -> Optional[AIProviderRoutingRule]:
        result = await self.db.execute(
            select(AIProviderRoutingRule).where(AIProviderRoutingRule.document_type == document_type)
        )
        return result.scalar_one_or_none()

    def add_routing_rule(self, rule: AIProviderRoutingRule):
        self.db.add(rule)
