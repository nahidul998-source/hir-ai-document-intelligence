from typing import List, Optional, Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.infrastructure.database.models import AuditLog, Document, Job

class MonitoringRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_audit_logs(self, skip: int, limit: int, action: Optional[str] = None) -> Tuple[int, List[AuditLog]]:
        query = select(AuditLog)
        if action:
            query = query.where(func.lower(AuditLog.action) == action.lower())
        
        query = query.order_by(desc(AuditLog.created_at))
        
        count_query = select(func.count()).select_from(query.subquery())
        total_res = await self.db.execute(count_query)
        total = total_res.scalar() or 0
        
        query = query.offset(skip).limit(limit)
        res = await self.db.execute(query)
        logs = list(res.scalars().all())
        
        return total, logs

    async def get_recent_documents(self, limit: int) -> List[Document]:
        query = select(Document).order_by(desc(Document.created_at)).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_job_status_counts(self) -> Dict[str, int]:
        count_query = select(Job.status, func.count(Job.id)).group_by(Job.status)
        count_res = await self.db.execute(count_query)
        return {row[0]: row[1] for row in count_res.all()}

    async def get_recent_jobs(self, limit: int) -> List[Job]:
        query = select(Job).order_by(desc(Job.created_at)).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())
