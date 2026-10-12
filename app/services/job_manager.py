import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from app.services.storage import storage
from app.models.schemas import JobStatus


class JobManager:
    """Manages background job state, progress reporting, and persistent serialization."""

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._listeners: Dict[str, list[asyncio.Queue]] = {}

    def create_job(self, job_id: str, filename: str) -> JobStatus:
        job_data = {
            "job_id": job_id,
            "filename": filename,
            "status": "uploading",
            "progress": 5,
            "message": "File received. Ready to extract.",
            "error": None,
            "total_pages": None,
            "ocr_pages_count": None,
            "total_words": None,
            "audio_url": None,
            "cleaned_text": None,
            "stats": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._jobs[job_id] = job_data
        storage.save_job_state_sync(job_id, job_data)
        return JobStatus(**job_data)

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
        **kwargs,
    ) -> None:
        if job_id not in self._jobs:
            self._jobs[job_id] = {"job_id": job_id}

        job = self._jobs[job_id]
        if status is not None:
            job["status"] = status
        if progress is not None:
            job["progress"] = progress
        if message is not None:
            job["message"] = message
        if error is not None:
            job["error"] = error

        for k, v in kwargs.items():
            job[k] = v

        job["updated_at"] = datetime.utcnow().isoformat()

        # Notify any active SSE subscribers
        if job_id in self._listeners:
            for queue in self._listeners[job_id]:
                try:
                    queue.put_nowait(dict(job))
                except Exception:
                    pass

        # Persist to disk/storage synchronously
        storage.save_job_state_sync(job_id, job)


    async def get_job(self, job_id: str) -> Optional[JobStatus]:
        if job_id in self._jobs:
            return JobStatus(**self._jobs[job_id])

        # Try loading from storage
        stored = await storage.get_job_state(job_id)
        if stored:
            self._jobs[job_id] = stored
            return JobStatus(**stored)

        return None

    def subscribe(self, job_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if job_id not in self._listeners:
            self._listeners[job_id] = []
        self._listeners[job_id].append(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        if job_id in self._listeners:
            if queue in self._listeners[job_id]:
                self._listeners[job_id].remove(queue)
            if not self._listeners[job_id]:
                del self._listeners[job_id]


job_manager = JobManager()
