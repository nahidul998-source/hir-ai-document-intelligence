import asyncio
import json
import logging
import aio_pika
import sys
import os

# Ensure backend can be imported

from adapters.webhook_erp_adapter import WebhookERPAdapter
from app.core.config import settings
from app.infrastructure.events.queue_topology import setup_queue_topology

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] ERP_WORKER: %(message)s"
)
logger = logging.getLogger(__name__)

RABBITMQ_URL = settings.RABBITMQ_URL

erp_adapter = WebhookERPAdapter()

async def process_erp_push(message: aio_pika.IncomingMessage) -> None:
    """Callback function for ERP integration."""
    async with message.process(requeue=False, reject_on_redelivered=False):
        try:
            payload = json.loads(message.body.decode("utf-8"))
            session_id = payload.get("session_id")
            transaction_type = payload.get("transaction_type", "LEGACY_PUSH")
            data = payload.get("data", {})
            
            logger.info(f"Received ERP push job for session {session_id}. Type: {transaction_type}")
            
            responses = []
            
            # Intelligent Routing
            if transaction_type == "CREATE_STYLE":
                res1 = await erp_adapter.create_style(data)
                responses.append(res1)
                
                # If BOM data exists, automatically spawn BOM creation
                if "BillOfMaterials" in data and data["BillOfMaterials"]:
                    res2 = await erp_adapter.create_bom(res1.get("erp_style_id", "UNKNOWN"), data["BillOfMaterials"])
                    responses.append(res2)
                    
            elif transaction_type == "CREATE_SALES_ORDER":
                res1 = await erp_adapter.create_sales_order(data)
                responses.append(res1)
                
            else:
                # Fallback for old schema
                res1 = await erp_adapter.push_data(session_id, payload)
                responses.append(res1)
                
            logger.info(f"ERP Push Successful for {session_id}: {responses}")
            
        except Exception as e:
            logger.error(f"Error handling ERP push: {e}")
            # The message will be nacked and because of DLX config, it will route to DLQ
            raise e

async def start_heartbeat():
    import redis.asyncio as aioredis
    from datetime import datetime
    logger.info("Starting ERP Worker heartbeat loop...")
    while True:
        try:
            client = aioredis.from_url(settings.REDIS_URL)
            await client.set("worker:heartbeat:erp_worker", datetime.utcnow().isoformat(), ex=30)
            await client.close()
        except Exception as e:
            logger.warning(f"Failed to record ERP Worker heartbeat: {e}")
        await asyncio.sleep(10)


async def main() -> None:
    logger.info("Starting HIR ERP Worker microservice...")
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
        logger.error("Could not connect to RabbitMQ. Exiting.")
        return

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    main_exchange, main_queue = await setup_queue_topology(
        channel=channel,
        service_name="erp_worker",
        routing_keys=["document.approved"]
    )

    logger.info("Listening for 'document.approved' events on 'hir.erp_worker.processing'...")
    await main_queue.consume(process_erp_push)

    # Start heartbeat task in background
    heartbeat_task = asyncio.create_task(start_heartbeat())

    try:
        await asyncio.Future()
    finally:
        heartbeat_task.cancel()
        await connection.close()

if __name__ == "__main__":
    asyncio.run(main())
