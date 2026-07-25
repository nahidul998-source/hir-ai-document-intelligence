import uuid
from contextvars import ContextVar
from typing import Optional

# Global context variable for multi-tenancy enforcement
tenant_context: ContextVar[Optional[uuid.UUID]] = ContextVar("tenant_context", default=None)
