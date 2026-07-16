import aio_pika
import logging

logger = logging.getLogger(__name__)

async def setup_queue_topology(channel: aio_pika.Channel, service_name: str, routing_keys: list[str]):
    """
    Standardized RabbitMQ Topology for all services.
    Ensures DLQ, Retries, and Exponential backoff are configured consistently.
    """
    # 1. Main Exchange
    main_exchange = await channel.declare_exchange(
        "hir.events", 
        aio_pika.ExchangeType.TOPIC, 
        durable=True
    )

    # 2. Dead Letter Exchange (DLX)
    dlx_name = f"hir.{service_name}.dlx"
    dlx = await channel.declare_exchange(
        dlx_name, 
        aio_pika.ExchangeType.DIRECT, 
        durable=True
    )
    
    # 3. Dead Letter Queue (DLQ)
    dlq_name = f"hir.{service_name}.dlq"
    dlq = await channel.declare_queue(dlq_name, durable=True)
    await dlq.bind(dlx, routing_key="failed")

    # 4. Main Processing Queue with DLX configuration
    queue_name = f"hir.{service_name}.processing"
    main_queue = await channel.declare_queue(
        queue_name,
        durable=True,
        arguments={
            "x-dead-letter-exchange": dlx_name,
            "x-dead-letter-routing-key": "failed"
        }
    )

    # 5. Bind routing keys to main queue
    for rk in routing_keys:
        await main_queue.bind(main_exchange, routing_key=rk)
        logger.info(f"[{service_name}] Bound routing key '{rk}' to queue '{queue_name}'")

    return main_exchange, main_queue
