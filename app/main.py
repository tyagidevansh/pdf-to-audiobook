import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    BASE_DIR,
    CURATED_VOICES,
    TTS_MODELS_INFO,
    MAX_UPLOAD_SIZE_MB,
    AUDIO_DIR,
)
from app.models.schemas import GenerateRequest, JobStatus
from app.services.storage import storage
from app.services.pdf_processor import pdf_processor
from app.services.tts_engine import tts_engine
from app.services.job_manager import job_manager

app = FastAPI(
    title="Audion - Smart PDF to Audiobook Studio",
    description="Convert any PDF (including scanned photos) into clear, natural audiobooks.",
    version="1.0.0",
)

# Allow CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static frontend
static_path = BASE_DIR / "static"
if not static_path.exists():
    static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

samples_path = BASE_DIR / "sample_pdfs"
if samples_path.exists():
    app.mount("/samples", StaticFiles(directory=str(samples_path)), name="samples")



@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Audion PDF to Audiobook API is running. Index file not found."}



@app.get("/api/voices")
async def get_voices():
    """Returns curated audiobook voices."""
    return CURATED_VOICES


@app.get("/api/config/models")
async def get_models_info():
    """Returns information about the app's free, built-in narration engine."""
    return TTS_MODELS_INFO


@app.post("/api/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    filter_headers_footers: bool = Form(True),
    filter_citations: bool = Form(True),
    unwrap_paragraphs: bool = Form(True),
):
    """
    Uploads a PDF, stores it via the storage provider, and begins asynchronous
    text extraction and smart layout cleaning.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    job_id = uuid.uuid4().hex
    content = await file.read()

    # Size check
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum upload size limit of {MAX_UPLOAD_SIZE_MB}MB.",
        )

    # Save to storage provider
    saved_path_str = await storage.save_upload(job_id, file.filename, content)
    pdf_path = Path(saved_path_str)

    job_manager.create_job(job_id, file.filename)
    job_manager.update_job(
        job_id,
        status="extracting",
        progress=10,
        message="Analyzing PDF structure and pages...",
    )

    # Launch extraction in background
    background_tasks.add_task(
        run_extraction_task,
        job_id=job_id,
        filename=file.filename,
        pdf_path=pdf_path,
        filter_headers_footers=filter_headers_footers,
        filter_citations=filter_citations,
        unwrap_paragraphs=unwrap_paragraphs,
    )

    return {"job_id": job_id, "filename": file.filename, "status": "extracting"}


async def run_extraction_task(
    job_id: str,
    filename: str,
    pdf_path: Path,
    filter_headers_footers: bool,
    filter_citations: bool,
    unwrap_paragraphs: bool,
):
    def on_progress(pct: int, msg: str):
        job_manager.update_job(job_id, progress=pct, message=msg)

    try:
        extract_result = await pdf_processor.extract_and_clean(
            job_id=job_id,
            filename=filename,
            pdf_path=pdf_path,
            progress_callback=on_progress,
            filter_headers_footers=filter_headers_footers,
            filter_citations=filter_citations,
            unwrap_paragraphs=unwrap_paragraphs,
        )

        job_manager.update_job(
            job_id,
            status="ready",
            progress=100,
            message="Document text ready for audiobook generation.",
            total_pages=extract_result.total_pages,
            ocr_pages_count=extract_result.ocr_pages_count,
            total_words=extract_result.total_words,
            cleaned_text=extract_result.cleaned_text,
            stats=extract_result.stats.model_dump(),
            estimated_duration=extract_result.estimated_duration_formatted,
        )

    except Exception as e:
        job_manager.update_job(
            job_id,
            status="failed",
            progress=100,
            message="Failed to process PDF.",
            error=str(e),
        )


@app.post("/api/generate")
async def generate_audiobook(
    req: GenerateRequest, background_tasks: BackgroundTasks
):
    """
    Initiates speech synthesis for the extracted or user-edited text.
    """
    job = await job_manager.get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    text_to_speak = req.text if req.text and req.text.strip() else job.cleaned_text
    if not text_to_speak or not text_to_speak.strip():
        raise HTTPException(status_code=400, detail="No readable text available to synthesize.")

    job_manager.update_job(
        req.job_id,
        status="generating",
        progress=5,
        message="Initiating speech synthesis...",
        cleaned_text=text_to_speak,
    )

    background_tasks.add_task(
        run_generation_task,
        job_id=req.job_id,
        text=text_to_speak,
        voice_id=req.voice_id,
        speed=req.speed,
    )

    return {"job_id": req.job_id, "status": "generating"}


async def run_generation_task(job_id: str, text: str, voice_id: str, speed: float):
    def on_progress(pct: int, msg: str):
        job_manager.update_job(job_id, progress=pct, message=msg)

    try:
        output_path = await storage.get_audio_path(job_id)
        await tts_engine.synthesize(
            job_id=job_id,
            text=text,
            voice_id=voice_id,
            speed=speed,
            output_path=output_path,
            progress_callback=on_progress,
        )

        audio_url = f"/api/audio/{job_id}"
        job_manager.update_job(
            job_id,
            status="completed",
            progress=100,
            message="Audiobook generation complete!",
            audio_url=audio_url,
        )

    except Exception as e:
        job_manager.update_job(
            job_id,
            status="failed",
            progress=100,
            message="Audio generation failed.",
            error=str(e),
        )


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Polls job status and progress."""
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.get("/api/jobs/{job_id}/events")
async def job_events_stream(job_id: str):
    """Server-Sent Events stream for instant progress updates."""
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    async def event_generator():
        # First send immediate current state
        yield f"data: {json.dumps(job.model_dump())}\n\n"
        if job.status in ("completed", "failed"):
            return

        queue = job_manager.subscribe(job_id)
        try:
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("status") in ("completed", "failed"):
                    break
        finally:
            job_manager.unsubscribe(job_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.api_route("/api/audio/{job_id}", methods=["GET", "HEAD"])
async def get_audio_file(job_id: str):

    """Streams or downloads the generated MP3 file."""
    audio_path = await storage.get_audio_path(job_id)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not ready or not found.")

    job = await job_manager.get_job(job_id)
    base_name = "audiobook"
    if job and job.filename:
        base_name = Path(job.filename).stem

    return FileResponse(
        str(audio_path),
        media_type="audio/mpeg",
        filename=f"{base_name}.mp3",
        headers={"Accept-Ranges": "bytes"},
    )


@app.get("/api/voices/{voice_id}/sample")
async def get_voice_sample(voice_id: str):
    """Returns or generates a short 3-second sample audio for previewing narrator voice."""
    sample_file = AUDIO_DIR / f"sample_{voice_id}.mp3"
    if not sample_file.exists():
        sample_text = "Call me Ishmael. Some years ago, having little or no money in my purse, I thought I would sail about a little."
        import edge_tts
        comm = edge_tts.Communicate(sample_text, voice_id)
        await comm.save(str(sample_file))

    return FileResponse(str(sample_file), media_type="audio/mpeg")
