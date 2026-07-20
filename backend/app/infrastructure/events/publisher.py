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
            # Declare processing queue
            await self.channel.declare_queue("hir.document.processing", durable=True)
            # Bind queue to exchange
            queue = await self.channel.get_queue("hir.document.processing")
            await queue.bind("hir.events", routing_key="document.uploaded")
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
        if not self.channel:
            await self.connect()

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
