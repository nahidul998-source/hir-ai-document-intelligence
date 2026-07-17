import logging
from typing import Any, Dict, Optional, Protocol
from app.infrastructure.events.publisher import RabbitMQEventPublisher

logger = logging.getLogger(__name__)


class IAlertingService(Protocol):
    """Protocol defining the alerting interface for clean architecture consistency."""

    async def trigger_alert(
        self,
        level: str,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Triggers an alert for system monitoring failures."""
        ...


class EventDrivenAlertingService(IAlertingService):
    """Observability Alerting Service that logs alerts and dispatches them via RabbitMQ."""

    def __init__(self, publisher: RabbitMQEventPublisher):
        self.publisher = publisher

    async def trigger_alert(
        self,
        level: str,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        alert_payload = {
            "level": level.upper(),  # WARNING, ERROR, CRITICAL
            "service": service,
            "message": message,
            "details": details or {},
        }
        
        # Log structured log record
        structured_msg = f"[ALERT] [{alert_payload['level']}] Service: {service} - Message: {message}"
        log_extra = {k: v for k, v in alert_payload.items() if k != "message"}
        if level.upper() in ("ERROR", "CRITICAL"):
            logger.error(structured_msg, extra=log_extra)
        else:
            logger.warning(structured_msg, extra=log_extra)

        # Dispatch event asynchronously
        try:
            # Avoid crashing health check loops if RabbitMQ is temporarily unreachable
            await self.publisher.publish_event(
                routing_key="system.alert",
                payload=alert_payload
            )
        except Exception as e:
            logger.warning(f"Could not publish alert event to RabbitMQ: {e}")
