import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
import aiofiles
from app.config import AUDIO_DIR, JOBS_DIR, UPLOAD_DIR


class StorageProvider(ABC):
    """Abstract storage interface for seamless future migration to S3, R2, or Supabase."""

    @abstractmethod
    async def save_upload(self, job_id: str, filename: str, content: bytes) -> str:
        """Saves an uploaded PDF and returns its persistent path or URL."""
        pass

    @abstractmethod
    async def get_upload_path(self, job_id: str) -> Path:
        """Retrieves local filepath for processing."""
        pass

    @abstractmethod
    async def save_audio(self, job_id: str, audio_bytes: bytes) -> str:
        """Saves generated MP3 and returns its path or public URL."""
        pass

    @abstractmethod
    async def get_audio_path(self, job_id: str) -> Path:
        """Retrieves audio filepath for streaming/download."""
        pass

    @abstractmethod
    async def save_job_state(self, job_id: str, state: Dict[str, Any]) -> None:
        """Saves persistent job metadata and progress."""
        pass

    @abstractmethod
    async def get_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves job metadata and progress."""
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage implementation for POC."""

    def __init__(self, upload_dir: Path = UPLOAD_DIR, audio_dir: Path = AUDIO_DIR, jobs_dir: Path = JOBS_DIR):
        self.upload_dir = upload_dir
        self.audio_dir = audio_dir
        self.jobs_dir = jobs_dir

    async def save_upload(self, job_id: str, filename: str, content: bytes) -> str:
        safe_ext = Path(filename).suffix or ".pdf"
        dest = self.upload_dir / f"{job_id}{safe_ext}"
        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)
        return str(dest)

    async def get_upload_path(self, job_id: str) -> Path:
        # Search for file matching job_id
        matches = list(self.upload_dir.glob(f"{job_id}.*"))
        if matches:
            return matches[0]
        return self.upload_dir / f"{job_id}.pdf"

    async def save_audio(self, job_id: str, audio_bytes: bytes) -> str:
        dest = self.audio_dir / f"{job_id}.mp3"
        async with aiofiles.open(dest, "wb") as f:
            await f.write(audio_bytes)
        return str(dest)

    async def get_audio_path(self, job_id: str) -> Path:
        return self.audio_dir / f"{job_id}.mp3"

    def save_job_state_sync(self, job_id: str, state: Dict[str, Any]) -> None:
        dest = self.jobs_dir / f"{job_id}.json"
        dest.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    async def save_job_state(self, job_id: str, state: Dict[str, Any]) -> None:
        self.save_job_state_sync(job_id, state)


    async def get_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        dest = self.jobs_dir / f"{job_id}.json"
        if not dest.exists():
            return None
        async with aiofiles.open(dest, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)


# Global default instance (can be replaced with S3StorageProvider when configured)
storage: StorageProvider = LocalStorageProvider()
