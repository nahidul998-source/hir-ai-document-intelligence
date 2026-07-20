import asyncio
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, fast-fail requests
    HALF_OPEN = "HALF_OPEN" # Testing recovery

class CircuitBreaker:
    """
    Advanced Circuit Breaker to wrap external dependencies (OpenAI, ERP).
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            logger.warning(f"Circuit Breaker OPEN. Request to {func.__name__} fast-failed.")
            raise Exception(f"Circuit Breaker OPEN for {func.__name__}")
            
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure()
            raise e
            
    async def _record_failure(self):
        async with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error("Circuit Breaker OPENED.")
                asyncio.create_task(self._attempt_recovery())
                
    async def _record_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit Breaker CLOSED and fully recovered.")
                
    async def _attempt_recovery(self):
        await asyncio.sleep(self.recovery_timeout)
        async with self._lock:
            self.state = CircuitState.HALF_OPEN
            logger.info("Circuit Breaker HALF_OPEN. Testing recovery...")
