import asyncio
from io import BytesIO
from typing import BinaryIO
from minio import Minio
from app.domain.interfaces import IStorageAdapter
from app.core.config import settings


class MinIOStorageAdapter(IStorageAdapter):
    """MinIO storage client executing block operations in thread pools for async safety."""

    def __init__(self):
        # Parse endpoint format (host:port)
        secure = settings.MINIO_SECURE
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=secure
        )
        self._is_degraded = False
        try:
            self._ensure_bucket(settings.MINIO_BUCKET_NAME)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Could not connect to MinIO on startup: {e}. Storage adapter running in degraded mode."
            )
            self._is_degraded = True

    def _ensure_bucket(self, bucket_name: str) -> None:
        """Helper to ensure target bucket exists."""
        if not self._is_degraded and not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    async def upload_file(self, bucket_name: str, object_name: str, data: BinaryIO, length: int, content_type: str) -> str:
        if self._is_degraded:
            import logging
            logging.getLogger(__name__).warning("Storage is in degraded mode. Skipping upload.")
            return object_name

        # Run synchronous MinIO calls inside threadpool to prevent blocking the async event loop
        def _upload():
            self._ensure_bucket(bucket_name)
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data,
                length=length,
                content_type=content_type
            )
            return object_name

        return await asyncio.to_thread(_upload)

    async def download_file(self, bucket_name: str, object_name: str) -> BinaryIO:
        def _download():
            response = self.client.get_object(bucket_name, object_name)
            data_stream = BytesIO(response.read())
            response.close()
            response.release_conn()
            return data_stream

        return await asyncio.to_thread(_download)

    async def delete_file(self, bucket_name: str, object_name: str) -> None:
        def _delete():
            self.client.remove_object(bucket_name, object_name)

        await asyncio.to_thread(_delete)

    async def get_presigned_url(self, bucket_name: str, object_name: str, expires_seconds: int = 3600) -> str:
        def _get_url():
            return self.client.get_presigned_url(
                method="GET",
                bucket_name=bucket_name,
                object_name=object_name,
                expires=asyncio.subprocess.sys.modules['datetime'].timedelta(seconds=expires_seconds)
            )

        # Minio Python SDK signature for timedelta requires importing datetime inside, let's write it cleanly
        import datetime
        def _get_url_clean():
            return self.client.get_presigned_url(
                method="GET",
                bucket_name=bucket_name,
                object_name=object_name,
                expires=datetime.timedelta(seconds=expires_seconds)
            )

        return await asyncio.to_thread(_get_url_clean)
