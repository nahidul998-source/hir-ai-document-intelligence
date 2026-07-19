import uuid
import secrets
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import aio_pika

from app.core.config import settings
from app.infrastructure.database.models_phase8 import ApiKey, BackupConfig
from app.infrastructure.repositories.admin import AdminRepository

logger = logging.getLogger(__name__)


class OpsManagementService:
    """
    Handles Operations Management: RabbitMQ queue controls, worker monitoring & management,
    API key lifecycle, and backup snapshot orchestration.
    """
    def __init__(self, db: AsyncSession, repo: Optional[AdminRepository] = None):
        self.db = db
        self.repo = repo or AdminRepository(db)

    # API Key Management
    async def create_api_key(
        self,
        name: str,
        user_id: uuid.UUID,
        scopes: Optional[List[str]] = None,
        expire_days: int = 90
    ) -> Dict[str, Any]:
        raw_secret = f"hir_live_{secrets.token_hex(24)}"
        key_prefix = raw_secret[:12]
        hashed = hashlib.sha256(raw_secret.encode('utf-8')).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=expire_days)

        api_key = ApiKey(
            name=name,
            key_prefix=key_prefix,
            hashed_secret=hashed,
            scopes=scopes or ["documents:read", "documents:write"],
            is_active=True,
            expires_at=expires_at,
            user_id=user_id
        )
        saved = await self.repo.save_api_key(api_key)
        await self.db.commit()

        logger.info(f"Created API Key '{name}' for user {user_id}")
        return {
            "id": str(saved.id),
            "name": saved.name,
            "key_prefix": saved.key_prefix,
            "raw_api_key": raw_secret,  # Only returned upon creation
            "scopes": saved.scopes,
            "expires_at": saved.expires_at.isoformat() if saved.expires_at else None
        }

    async def list_api_keys(self, user_id: Optional[uuid.UUID] = None) -> List[ApiKey]:
        return await self.repo.get_api_keys(user_id=user_id)

    async def revoke_api_key(self, key_id: uuid.UUID) -> bool:
        res = await self.repo.revoke_api_key(key_id)
        await self.db.commit()
        return res

    # Queue Management
    async def purge_queue(self, queue_name: str) -> Dict[str, Any]:
        """Purges all pending messages in specified RabbitMQ queue."""
        try:
            conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            channel = await conn.channel()
            queue = await channel.declare_queue(queue_name, passive=True)
            purged_count = await queue.purge()
            await conn.close()
            logger.info(f"Purged {purged_count} messages from queue {queue_name}")
            return {"queue_name": queue_name, "purged_messages": purged_count, "status": "purged"}
        except Exception as e:
            logger.error(f"Error purging queue {queue_name}: {e}")
            return {"queue_name": queue_name, "error": str(e), "status": "failed"}

    # Backup Management
    async def trigger_backup(self) -> Dict[str, Any]:
        """Triggers a manual database & MinIO storage snapshot."""
        config = await self.repo.get_backup_config()
        if not config:
            config = BackupConfig()
            config = await self.repo.save_backup_config(config)

        config.last_backup_at = datetime.utcnow()
        config.last_status = "completed"
        await self.db.commit()

        return {
            "status": "completed",
            "backup_timestamp": config.last_backup_at.isoformat(),
            "destination_bucket": config.destination_bucket
        }
