import asyncio
import json
import logging
import aio_pika

from app.infrastructure.adapters.ai_provider_manager import AIProviderManager
from ai.worker.pipeline.document_processor import DocumentProcessor
from app.core.settings import settings
from app.infrastructure.events.queue_topology import setup_queue_topology

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] AI_WORKER: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize global singletons
ai_provider_manager = AIProviderManager()
document_processor = DocumentProcessor(ai_provider_manager)

RABBITMQ_URL = settings.queue.url


async def publish_event(channel: aio_pika.Channel, routing_key: str, payload: dict):
    exchange = await channel.get_exchange("hir.events")
    await exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=routing_key
    )

async def handle_document_uploaded(message: aio_pika.IncomingMessage) -> None:
    """1. Classification Phase"""
    async with message.process():
        try:
            payload = json.loads(message.body.decode("utf-8"))
            document_id = payload.get("document_id")
            filename = payload.get("filename")
            minio_key = payload.get("minio_key")
            logger.info(f"Classification Worker handling document: {document_id}")
            
            import httpx
            from app.infrastructure.adapters.storage.minio_adapter import MinIOStorageAdapter
            from app.core.config import settings
            
            logger.info(f"Downloading {filename} for classification...")
            storage_adapter = MinIOStorageAdapter()
            file_stream = await storage_adapter.download_file(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=minio_key
            )
            file_bytes = file_stream.read()
            
            # Fast text extraction for classification
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            first_page_text = doc[0].get_text() if len(doc) > 0 else ""
            doc.close()
            
            # Classify using AI orchestrator
            from ai.worker.classifiers.document_classifier import DocumentClassifier
            classifier = DocumentClassifier(ai_orchestrator=document_processor.orchestrator)
            classification_result = await classifier.classify(filename, first_page_text)
            
            # Emit document.classified event
            await publish_event(message.channel, "document.classified", {
                "document_id": document_id,
                "minio_key": minio_key,
                "filename": filename,
                "document_type": classification_result.get("document_type", "generic")
            })
        except Exception as e:
            logger.error(f"Error in Classification Worker: {e}")
            raise

async def handle_document_classified(message: aio_pika.IncomingMessage) -> None:
    """2. OCR & Layout Phase"""
    async with message.process():
        try:
            payload = json.loads(message.body.decode("utf-8"))
            document_id = payload.get("document_id")
            filename = payload.get("filename")
            minio_key = payload.get("minio_key")
            doc_type = payload.get("document_type")
            logger.info(f"OCR Worker handling document: {document_id}")
            
            from app.infrastructure.adapters.storage.minio_adapter import MinIOStorageAdapter
            from app.core.config import settings
            
            storage_adapter = MinIOStorageAdapter()
            file_stream = await storage_adapter.download_file(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=minio_key
            )
            file_bytes = file_stream.read()
            
            ocr_result = await document_processor.extract_text_and_layout(filename, file_bytes)
            
            # In a real app we'd save layout to DB here. For now, pass text forward.
            await publish_event(message.channel, "ocr.completed", {
                "document_id": document_id,
                "document_type": doc_type,
                "extracted_text": ocr_result["text"]
            })
        except Exception as e:
            logger.error(f"Error in OCR Worker: {e}")
            raise

async def handle_ocr_completed(message: aio_pika.IncomingMessage) -> None:
    """3. Extraction & Validation Phase"""
    async with message.process():
        try:
            payload = json.loads(message.body.decode("utf-8"))
            document_id = payload.get("document_id")
            doc_type = payload.get("document_type")
            extracted_text = payload.get("extracted_text")
            logger.info(f"Extraction Worker handling document: {document_id}")
            
            from app.database.session import async_session_maker
            import httpx
            
            async with async_session_maker() as db:
                result = await document_processor.extract_data(
                    filename="extracted.pdf",
                    extracted_text=extracted_text,
                    doc_type=doc_type,
                    db=db
                )
                
                logger.info(f"Persisting extraction results for document: {document_id}")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"http://localhost:8002/api/v1/documents/{document_id}/extraction",
                        json={
                            "extracted_data": result.get("extracted_data"),
                            "document_type": result.get("classifier_result"),
                            "confidence_metadata": result.get("confidence_metadata")
                        }
                    )
                    response.raise_for_status()
                
            logger.info(f"Extraction complete for {document_id}")
        except Exception as e:
            logger.error(f"Error in Extraction Worker: {e}")
            raise


async def start_heartbeat():
    import redis.asyncio as aioredis
    from datetime import datetime
    logger.info("Starting AI Worker heartbeat loop...")
    while True:
        try:
            client = aioredis.from_url(settings.REDIS_URL)
            await client.set("worker:heartbeat:ai_worker", datetime.utcnow().isoformat(), ex=30)
            await client.close()
        except Exception as e:
            logger.warning(f"Failed to record AI Worker heartbeat: {e}")
        await asyncio.sleep(10)


async def main() -> None:
    logger.info("Starting HIR standalone AI Worker microservice...")
    connection = None
    retries = 5
    while retries > 0:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            break
        except Exception as e:
            logger.warning(f"RabbitMQ connection failed: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
            retries -= 1

    if not connection:
        logger.error("Could not connect to RabbitMQ. Standalone worker exiting.")
        return

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    # 1. Classification Worker
    _, class_queue = await setup_queue_topology(
        channel=channel,
        service_name="ai_worker_classifier",
        routing_keys=["document.uploaded"]
    )
    
    # 2. OCR Worker
    _, ocr_queue = await setup_queue_topology(
        channel=channel,
        service_name="ai_worker_ocr",
        routing_keys=["document.classified"]
    )
    
    # 3. Extraction Worker
    _, ext_queue = await setup_queue_topology(
        channel=channel,
        service_name="ai_worker_extractor",
        routing_keys=["ocr.completed"]
    )

    logger.info("Listening for multiple events on RabbitMQ (Classification, OCR, Extraction)...")
    await class_queue.consume(handle_document_uploaded)
    await ocr_queue.consume(handle_document_classified)
    await ext_queue.consume(handle_ocr_completed)

    # Start heartbeat task in background
    heartbeat_task = asyncio.create_task(start_heartbeat())

    try:
        await asyncio.Future()
    finally:
        heartbeat_task.cancel()
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
