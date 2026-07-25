import json
import logging
import asyncio
import aio_pika
from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQEventPublisher:
    """Publishes domain events to RabbitMQ exchange for consumption by the AI processing microservice."""

    def __init__(self):
        self.url = settings.RABBITMQ_URL
        self.connection = None
        self.channel = None

    async def connect(self) -> None:
        """Establishes connection to RabbitMQ Broker."""
        try:
            self.connection = await asyncio.wait_for(aio_pika.connect(self.url, timeout=2.0), timeout=2.0)
            self.channel = await self.connection.channel()
            # Declare durable exchange for domain events
            await self.channel.declare_exchange("hir.events", aio_pika.ExchangeType.TOPIC, durable=True)
            
            # Setup the same topology as the AI worker to ensure messages aren't lost if worker is offline
            from app.infrastructure.events.queue_topology import setup_queue_topology
            await setup_queue_topology(self.channel, "ai_worker_classifier", ["document.uploaded"])
            await setup_queue_topology(self.channel, "ai_worker_ocr", ["document.classified"])
            await setup_queue_topology(self.channel, "ai_worker_extractor", ["ocr.completed"])
            
            logger.info("Successfully connected to RabbitMQ broker and initialized exchanges/queues.")
        except Exception as e:
            logger.warning(f"RabbitMQ connection skipped: {e}")
            self.connection = None
            self.channel = None

    async def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def publish_event(self, routing_key: str, payload: dict) -> None:
        """Publishes an event to RabbitMQ."""
        if not self.connection or self.connection.is_closed or not self.channel or self.channel.is_closed:
            await self.connect()

        if not self.channel or self.channel.is_closed:
            logger.error("Failed to establish RabbitMQ channel.")
            raise ConnectionError("RabbitMQ channel not available")

        try:
            body = json.dumps(payload).encode("utf-8")
            message = aio_pika.Message(
                body=body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            exchange = await self.channel.get_exchange("hir.events")
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f"Published event '{routing_key}' with payload: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish event to RabbitMQ: {e}")
            raise
