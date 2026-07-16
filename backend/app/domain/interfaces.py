import uuid
from typing import BinaryIO, Dict, Any, Optional, Protocol


class IStorageAdapter(Protocol):
    """Abstract protocol for file storage (MinIO, S3, Local, etc.) conforming to Clean Architecture."""

    async def upload_file(self, bucket_name: str, object_name: str, data: BinaryIO, length: int, content_type: str) -> str:
        """Uploads a file and returns the file path/key."""
        ...

    async def download_file(self, bucket_name: str, object_name: str) -> BinaryIO:
        """Downloads a file and returns a binary stream."""
        ...

    async def delete_file(self, bucket_name: str, object_name: str) -> None:
        """Deletes a file from the storage."""
        ...

    async def get_presigned_url(self, bucket_name: str, object_name: str, expires_seconds: int = 3600) -> str:
        """Gets a presigned download URL for frontend client display."""
        ...


class INotificationAdapter(Protocol):
    """Abstract protocol for notifications (Email, Slack, Webhook)."""

    async def send(self, recipient: str, title: str, body: str) -> None:
        """Sends a notification message."""
        ...


class IAIProvider(Protocol):
    """Abstract interface for LLM / AI Model Providers (Local Qwen, GitHub Models, Gemini)."""

    async def generate_json(self, prompt: str, schema: Dict[str, Any], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generates a structured JSON response matching the provided schema."""
        ...

    async def is_healthy(self) -> bool:
        """Checks if the provider endpoint is healthy and online."""
        ...
