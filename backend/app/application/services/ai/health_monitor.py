import asyncio
import logging
from typing import Optional
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager

logger = logging.getLogger(__name__)

class AIProviderHealthMonitor:
    """
    Dedicated background monitoring service for AI Providers.
    Pings all providers at a configurable interval to track live health status and uptime metrics.
    """

    def __init__(self, manager: AIProviderManager, interval_seconds: int = 60):
        self.manager = manager
        self.interval_seconds = interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the background health checking loop."""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"AI Provider Health Monitor started (Interval: {self.interval_seconds}s).")

    async def stop(self) -> None:
        """Stop the background health checking loop."""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AI Provider Health Monitor stopped.")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self.manager.initialize()
                logger.debug("Executing background health checks for all AI Providers...")
                await self.manager.ping_all_providers()
            except Exception as e:
                logger.error(f"Error executing AI Provider health check loop: {e}", exc_info=True)
            
            await asyncio.sleep(self.interval_seconds)
