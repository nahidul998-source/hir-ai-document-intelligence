import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    LearningCorrectionRecord,
    LearningDataset,
    LearningDatasetItem,
    PromptOptimizationRecord,
    AIFeedbackMetric
)


class LearningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_correction_record(self, record: LearningCorrectionRecord) -> LearningCorrectionRecord:
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_correction_records(
        self,
        skip: int = 0,
        limit: int = 50,
        document_type: Optional[str] = None,
        field_name: Optional[str] = None,
        was_modified: Optional[bool] = None,
        buyer_code: Optional[str] = None
    ) -> List[LearningCorrectionRecord]:
        query = select(LearningCorrectionRecord)
        if document_type:
            query = query.where(LearningCorrectionRecord.document_type == document_type)
        if field_name:
            query = query.where(LearningCorrectionRecord.field_name == field_name)
        if was_modified is not None:
            query = query.where(LearningCorrectionRecord.was_modified == was_modified)
        if buyer_code:
            query = query.where(LearningCorrectionRecord.buyer_code == buyer_code)

        query = query.order_by(desc(LearningCorrectionRecord.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_correction_records(
        self,
        document_type: Optional[str] = None,
        field_name: Optional[str] = None,
        was_modified: Optional[bool] = None,
        buyer_code: Optional[str] = None
    ) -> int:
        query = select(func.count(LearningCorrectionRecord.id))
        if document_type:
            query = query.where(LearningCorrectionRecord.document_type == document_type)
        if field_name:
            query = query.where(LearningCorrectionRecord.field_name == field_name)
        if was_modified is not None:
            query = query.where(LearningCorrectionRecord.was_modified == was_modified)
        if buyer_code:
            query = query.where(LearningCorrectionRecord.buyer_code == buyer_code)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create_dataset(self, dataset: LearningDataset) -> LearningDataset:
        self.db.add(dataset)
        await self.db.flush()
        return dataset

    async def add_dataset_item(self, item: LearningDatasetItem) -> LearningDatasetItem:
        self.db.add(item)
        await self.db.flush()
        return item

    async def get_dataset_by_id(self, dataset_id: uuid.UUID) -> Optional[LearningDataset]:
        query = select(LearningDataset).where(LearningDataset.id == dataset_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_datasets(self, skip: int = 0, limit: int = 50) -> List[LearningDataset]:
        query = select(LearningDataset).order_by(desc(LearningDataset.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_dataset_items(self, dataset_id: uuid.UUID) -> List[LearningDatasetItem]:
        query = select(LearningDatasetItem).where(LearningDatasetItem.dataset_id == dataset_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def save_prompt_optimization(self, record: PromptOptimizationRecord) -> PromptOptimizationRecord:
        if record.is_active:
            # deactivate other records with same prompt_name
            await self.db.execute(
                update(PromptOptimizationRecord)
                .where(PromptOptimizationRecord.prompt_name == record.prompt_name)
                .values(is_active=False)
            )
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_active_prompt(self, prompt_name: str) -> Optional[PromptOptimizationRecord]:
        query = select(PromptOptimizationRecord).where(
            PromptOptimizationRecord.prompt_name == prompt_name,
            PromptOptimizationRecord.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_prompt_history(self, prompt_name: str) -> List[PromptOptimizationRecord]:
        query = select(PromptOptimizationRecord).where(
            PromptOptimizationRecord.prompt_name == prompt_name
        ).order_by(desc(PromptOptimizationRecord.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def save_feedback_metric(self, metric: AIFeedbackMetric) -> AIFeedbackMetric:
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def get_recent_feedback_metrics(self, field_name: Optional[str] = None, limit: int = 30) -> List[AIFeedbackMetric]:
        query = select(AIFeedbackMetric)
        if field_name:
            query = query.where(AIFeedbackMetric.field_name == field_name)
        query = query.order_by(desc(AIFeedbackMetric.time_bucket)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
