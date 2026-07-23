import asyncio
import time
import uuid
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.infrastructure.adapters.storage.minio_adapter import MinIOStorageAdapter
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager
from ai.worker.pipeline.document_processor import DocumentProcessor
from ai.worker.classifiers.document_classifier import DocumentClassifier
from app.database.session import async_session_maker
from app.core.config import settings
from sqlalchemy.future import select
from app.infrastructure.database.models import Document

async def generate_mock_pdf() -> bytes:
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), "TECH PACK - SPRING COLLECTION")
    page.insert_text(fitz.Point(50, 70), "Garment: T-Shirt")
    page.insert_text(fitz.Point(50, 90), "Buyer: H&M")
    
    # Mock a table
    page.insert_text(fitz.Point(50, 120), "Fabric Consumption Table:")
    page.insert_text(fitz.Point(50, 140), "Fabric | Color | Consumption")
    page.insert_text(fitz.Point(50, 160), "Cotton | White | 1.2 kg")
    
    # Actually draw some lines for the table so fitz can find it
    page.draw_line(fitz.Point(50, 135), fitz.Point(250, 135))
    page.draw_line(fitz.Point(50, 155), fitz.Point(250, 155))
    
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

async def run_verification():
    print("==================================================")
    print("   HIR END-TO-END RUNTIME VERIFICATION (PHASE 2.5)  ")
    print("==================================================")
    
    # Initialize components
    ai_provider = AIProviderManager()
    document_processor = DocumentProcessor(ai_provider)
    classifier = DocumentClassifier(ai_orchestrator=document_processor.orchestrator)
    storage = MinIOStorageAdapter()
    
    document_id = str(uuid.uuid4())
    filename = "test_tech_pack.pdf"
    minio_key = f"uploads/{document_id}/{filename}"
    
    print("\n[Stage 1: Upload]")
    start = time.time()
    pdf_bytes = await generate_mock_pdf()
    
    import io
    pdf_stream = io.BytesIO(pdf_bytes)
    await storage.upload_file(settings.MINIO_BUCKET_NAME, minio_key, pdf_stream, len(pdf_bytes), "application/pdf")
    
    upload_time = time.time() - start
    print(f"[SUCCESS] Success ({upload_time:.3f}s)")
    print(f"   Input: Mock PDF Data")
    print(f"   Output: Persisted to MinIO ({minio_key})")
    
    print("\n[Stage 2: Classification (Zero-Shot LLM)]")
    start = time.time()
    first_page_text = "TECH PACK - SPRING COLLECTION\nGarment: T-Shirt\nBuyer: H&M"
    classification_res = await classifier.classify(filename, first_page_text)
    class_time = time.time() - start
    doc_type = classification_res.get("document_type", "unknown")
    print(f"[SUCCESS] Success ({class_time:.3f}s)")
    print(f"   Input: filename={filename}, text='TECH PACK...'")
    print(f"   Output: {classification_res}")
    
    print("\n[Stage 3: Hybrid OCR & Layout Engine]")
    start = time.time()
    ocr_res = await document_processor.extract_text_and_layout(filename, pdf_bytes)
    ocr_time = time.time() - start
    print(f"[SUCCESS] Success ({ocr_time:.3f}s)")
    print(f"   Input: PDF Bytes ({len(pdf_bytes)} bytes)")
    print(f"   Output: {len(ocr_res['text'])} chars text, {len(ocr_res['layout_blocks'])} layout blocks, {len(ocr_res['tables'])} tables found")
    if len(ocr_res['tables']) > 0:
        print(f"   Table 0 BBox: {ocr_res['tables'][0]['bbox']}")
    
    print("\n[Stage 4: LLM Extraction, Validation & Confidence]")
    start = time.time()
    async with async_session_maker() as db:
        extract_res = await document_processor.extract_data(
            filename=filename,
            extracted_text=ocr_res["text"],
            doc_type=doc_type,
            db=db
        )
    extract_time = time.time() - start
    print(f"[SUCCESS] Success ({extract_time:.3f}s)")
    print(f"   Input: doc_type={doc_type}, ocr_text_length={len(ocr_res['text'])}")
    print(f"   Output Validated Fields: {list(extract_res['extracted_data'].keys())}")
    print(f"   Validation Status: Schema={extract_res['is_schema_valid']}, Pydantic={extract_res['is_pydantic_valid']}, Business={extract_res['is_business_valid']}")
    
    print("\n[Stage 5: Confidence Engine Evaluation]")
    conf_keys = list(extract_res["confidence_metadata"].keys())
    print(f"[SUCCESS] Success")
    print(f"   Evaluated {len(conf_keys)} fields.")
    if conf_keys:
        sample_key = conf_keys[0]
        print(f"   Sample Confidence [{sample_key}]: {extract_res['confidence_metadata'][sample_key]['confidence_score']} ({extract_res['confidence_metadata'][sample_key]['validation_status']})")
    
    print("\n==================================================")
    print(" VERIFICATION COMPLETE")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_verification())
