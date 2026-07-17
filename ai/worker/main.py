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


async def process_document_uploaded(message: aio_pika.IncomingMessage) -> None:
    """Callback function triggered when a new document is uploaded to RabbitMQ."""
    async with message.process():
        try:
            payload = json.loads(message.body.decode("utf-8"))
            filename = payload.get("filename", "unknown.pdf")
            logger.info(f"Received document processing job. Payload: {payload}")
            
            # Phase 2 Processing Pipeline
            logger.info("Initializing Phase 2 Processing Pipeline...")
            
            result = await document_processor.process_document(
                filename=filename, 
                first_page_text=""
            )
            
            logger.info(f"Pipeline Result Status - Valid: {result.get('is_valid')}")
            logger.info(f"Classifier Result: {result.get('classifier_result')}")
            logger.info(f"Job completed successfully for document: {payload.get('document_id')}")
            
            # The result is ready to be stored in the DB (next step in Phase 3/2 completion)
        except Exception as e:
            logger.error(f"Error handling document upload processing: {e}")


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
    # Configure prefetch count (process 1 message at a time to distribute CPU load)
    await channel.set_prefetch(prefetch_count=1)

    # Use standardized topology
    main_exchange, main_queue = await setup_queue_topology(
        channel=channel,
        service_name="ai_worker",
        routing_keys=["document.uploaded"]
    )

    logger.info("Listening for document upload events on RabbitMQ queue 'hir.ai_worker.processing'...")
    await main_queue.consume(process_document_uploaded)

    # Start heartbeat task in background
    heartbeat_task = asyncio.create_task(start_heartbeat())

    try:
        # Keep running
        await asyncio.Future()
    finally:
        heartbeat_task.cancel()
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
