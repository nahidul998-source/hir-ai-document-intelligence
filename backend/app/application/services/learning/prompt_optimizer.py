import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models_phase7 import PromptOptimizationRecord, LearningCorrectionRecord
from app.infrastructure.repositories.learning import LearningRepository

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """
    Module 3: Prompt Optimizer
    Evaluates system prompts, generates dynamic few-shot prompt exemplars,
    and manages system prompt versioning and accuracy improvements.
    """
    def __init__(self, db: AsyncSession, repo: Optional[LearningRepository] = None):
        self.db = db
        self.repo = repo or LearningRepository(db)

    async def generate_few_shot_exemplars(self, field_name: Optional[str] = None, max_samples: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves top approved human corrections to serve as high-quality few-shot exemplars in prompt injections.
        """
        records = await self.repo.get_correction_records(
            skip=0,
            limit=max_samples * 2,
            field_name=field_name,
            was_modified=True
        )

        exemplars = []
        for r in records[:max_samples]:
            exemplars.append({
                "field_name": r.field_name,
                "input_snippet": r.ocr_context_snippet or f"Extracted value: {r.original_extracted_value}",
                "corrected_value": r.corrected_value,
                "confidence": r.initial_confidence
            })
        return exemplars

    async def create_prompt_version(
        self,
        prompt_name: str,
        version: str,
        template_content: str,
        few_shot_exemplars: Optional[List[Dict[str, Any]]] = None,
        is_active: bool = True,
        notes: Optional[str] = None
    ) -> PromptOptimizationRecord:
        """
        Registers a new prompt template version with specified exemplars and activates it.
        """
        record = PromptOptimizationRecord(
            prompt_name=prompt_name,
            version=version,
            template_content=template_content,
            few_shot_exemplars=few_shot_exemplars or [],
            eval_accuracy_score=None,
            eval_sample_count=0,
            is_active=is_active,
            notes=notes
        )
        saved_prompt = await self.repo.save_prompt_optimization(record)
        await self.db.commit()
        logger.info(f"Created and saved prompt optimization '{prompt_name}' version {version}")
        return saved_prompt

    async def evaluate_prompt_accuracy(self, prompt_name: str, version: str) -> Dict[str, Any]:
        """
        Evaluates accuracy score for a prompt version against captured learning records.
        """
        prompt = await self.repo.get_active_prompt(prompt_name)
        total_records = await self.repo.count_correction_records()
        modified_records = await self.repo.count_correction_records(was_modified=True)

        if total_records == 0:
            accuracy = 1.0
        else:
            accuracy = round(1.0 - (modified_records / total_records), 4)

        if prompt:
            prompt.eval_accuracy_score = accuracy
            prompt.eval_sample_count = total_records
            await self.repo.save_prompt_optimization(prompt)
            await self.db.commit()

        return {
            "prompt_name": prompt_name,
            "version": version,
            "eval_accuracy_score": accuracy,
            "eval_sample_count": total_records,
            "uncorrected_rate": accuracy
        }
