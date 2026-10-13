from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VoiceInfo(BaseModel):
    id: str
    name: str
    gender: str
    accent: str
    style: str
    description: str
    recommended: bool = False


class PageBlock(BaseModel):
    page_number: int
    is_ocr: bool
    text: str
    char_count: int


class CleaningStats(BaseModel):
    headers_removed: int = 0
    footers_removed: int = 0
    page_numbers_removed: int = 0
    citations_removed: int = 0
    book_matter_pages_removed: int = 0
    hyphens_fixed: int = 0
    paragraphs_formatted: int = 0


class ExtractResponse(BaseModel):
    job_id: str
    filename: str
    total_pages: int
    ocr_pages_count: int
    total_words: int
    estimated_duration_seconds: int
    estimated_duration_formatted: str
    cleaned_text: str
    pages: List[PageBlock]
    stats: CleaningStats


class GenerateRequest(BaseModel):
    job_id: str
    text: Optional[str] = None
    voice_id: str = "en-US-AriaNeural"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: str = "+0Hz"


class JobStatus(BaseModel):
    job_id: str
    status: str  # "extracting", "ready", "generating", "completed", "failed"
    progress: int = 0
    message: str = ""
    error: Optional[str] = None
    filename: Optional[str] = None
    total_pages: Optional[int] = None
    ocr_pages_count: Optional[int] = None
    total_words: Optional[int] = None
    audio_url: Optional[str] = None
    cleaned_text: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None

