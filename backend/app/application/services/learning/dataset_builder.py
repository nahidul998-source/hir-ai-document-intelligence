import uuid
import json
import csv
import io
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    LearningCorrectionRecord,
    LearningDataset,
    LearningDatasetItem
)
from app.infrastructure.repositories.learning import LearningRepository

logger = logging.getLogger(__name__)


class DatasetBuilder:
    """
    Module 2: Dataset Builder
    Compiles captured learning records into fine-tuning datasets (JSONL format for OpenAI, Anthropic, LLaMA)
    and Few-Shot exemplar sets.
    """
    def __init__(self, db: AsyncSession, repo: Optional[LearningRepository] = None):
        self.db = db
        self.repo = repo or LearningRepository(db)

    async def build_dataset(
        self,
        name: str,
        description: str,
        dataset_type: str = "fine_tuning_jsonl",
        document_type: Optional[str] = None,
        target_field: Optional[str] = None,
        min_confidence_threshold: float = 0.0,
        only_modified: bool = False
    ) -> LearningDataset:
        """
        Queries matching correction records and constructs a new LearningDataset with items.
        """
        # Fetch candidate records
        records = await self.repo.get_correction_records(
            skip=0,
            limit=500,
            document_type=document_type,
            field_name=target_field,
            was_modified=True if only_modified else None
        )

        dataset = LearningDataset(
            name=name,
            description=description,
            dataset_type=dataset_type,
            document_type=document_type,
            target_field=target_field,
            min_confidence_threshold=min_confidence_threshold,
            sample_count=0,
            status="building"
        )
        created_dataset = await self.repo.create_dataset(dataset)

        items_count = 0
        for rec in records:
            if rec.initial_confidence and rec.initial_confidence < min_confidence_threshold:
                continue

            # Format input/output based on dataset type
            if dataset_type == "fine_tuning_jsonl":
                input_prompt = json.dumps({
                    "system": "You are an AI Document Extraction Specialist for garment manufacturing tech packs and purchase orders.",
                    "user": f"Extract field '{rec.field_name}' from the following snippet: {rec.ocr_context_snippet or rec.original_extracted_value}"
                })
                target_output = json.dumps({
                    rec.field_name: rec.corrected_value
                })
            else:  # few_shot_prompt
                input_prompt = f"Field: {rec.field_name}\nContext: {rec.ocr_context_snippet}"
                target_output = f"Extracted Value: {rec.corrected_value}"

            item = LearningDatasetItem(
                dataset_id=created_dataset.id,
                correction_record_id=rec.id,
                input_prompt=input_prompt,
                target_output=target_output,
                quality_score=1.0 if rec.was_modified else 0.9
            )
            await self.repo.add_dataset_item(item)
            items_count += 1

        created_dataset.sample_count = items_count
        created_dataset.status = "ready"
        created_dataset.export_metadata = {
            "created_at": created_dataset.created_at.isoformat() if created_dataset.created_at else None,
            "format": dataset_type,
            "total_items": items_count
        }

        await self.db.commit()
        logger.info(f"Built dataset '{name}' (ID: {created_dataset.id}) with {items_count} items.")
        return created_dataset

    async def export_dataset_content(self, dataset_id: uuid.UUID, export_format: str = "jsonl") -> str:
        """
        Exports dataset items into JSONL, JSON, or CSV raw text format.
        """
        dataset = await self.repo.get_dataset_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with ID {dataset_id} not found.")

        items = await self.repo.get_dataset_items(dataset_id)

        if export_format.lower() == "jsonl":
            lines = []
            for item in items:
                try:
                    p_obj = json.loads(item.input_prompt)
                    o_obj = json.loads(item.target_output)
                    line_data = {
                        "messages": [
                            {"role": "system", "content": p_obj.get("system", "")},
                            {"role": "user", "content": p_obj.get("user", "")},
                            {"role": "assistant", "content": json.dumps(o_obj)}
                        ]
                    }
                    lines.append(json.dumps(line_data))
                except Exception:
                    line_data = {
                        "prompt": item.input_prompt,
                        "completion": item.target_output
                    }
                    lines.append(json.dumps(line_data))
            return "\n".join(lines)

        elif export_format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["id", "input_prompt", "target_output", "quality_score"])
            for item in items:
                writer.writerow([str(item.id), item.input_prompt, item.target_output, item.quality_score])
            return output.getvalue()

        else:  # json
            result = [
                {
                    "id": str(item.id),
                    "input_prompt": item.input_prompt,
                    "target_output": item.target_output,
                    "quality_score": item.quality_score
                }
                for item in items
            ]
            return json.dumps(result, indent=2)
