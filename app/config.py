import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

UPLOAD_DIR = DATA_DIR / "uploads"
AUDIO_DIR = DATA_DIR / "audio"
JOBS_DIR = DATA_DIR / "jobs"

for path in [UPLOAD_DIR, AUDIO_DIR, JOBS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE_MB = 100
DEFAULT_OCR_DPI = 200

# High-fidelity voices curated specifically for audiobooks
CURATED_VOICES = [
    {
        "id": "en-US-AriaNeural",
        "name": "Aria",
        "gender": "Female",
        "accent": "US",
        "style": "Expressive Storyteller",
        "description": "Rich emotional range, ideal for fiction, drama, and narrative novels.",
        "recommended": True
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy",
        "gender": "Male",
        "accent": "US",
        "style": "Deep Classic Narrator",
        "description": "Resonant, authoritative, and smooth. Classic audiobook narrator voice.",
        "recommended": True
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher",
        "gender": "Male",
        "accent": "US",
        "style": "Warm & Engaging",
        "description": "Warm, measured pacing, perfect for memoirs, non-fiction, and sci-fi.",
        "recommended": False
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny",
        "gender": "Female",
        "accent": "US",
        "style": "Clear & Natural",
        "description": "Crisp, pleasant, and easy to follow. Ideal for business and science.",
        "recommended": False
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan",
        "gender": "Male",
        "accent": "British",
        "style": "Literary & Refined",
        "description": "Classic British RP narrator. Elegant cadence for literature and history.",
        "recommended": False
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia",
        "gender": "Female",
        "accent": "British",
        "style": "Gentle & Poetic",
        "description": "Soothing British accent, wonderful for fantasy, poetry, and calm reads.",
        "recommended": False
    },
    {
        "id": "en-US-AndrewMultilingualNeural",
        "name": "Andrew",
        "gender": "Male",
        "accent": "US",
        "style": "Conversational & Sincere",
        "description": "Modern conversational tone, authentic and easygoing.",
        "recommended": False
    },
    {
        "id": "en-US-AvaMultilingualNeural",
        "name": "Ava",
        "gender": "Female",
        "accent": "US",
        "style": "Bright & Versatile",
        "description": "A lively, polished voice with a modern, adaptable delivery.",
        "recommended": False
    },
    {
        "id": "en-US-EmmaMultilingualNeural",
        "name": "Emma",
        "gender": "Female",
        "accent": "US",
        "style": "Warm & Conversational",
        "description": "Relaxed and reassuring, with a natural conversational rhythm.",
        "recommended": False
    },
    {
        "id": "en-US-BrianMultilingualNeural",
        "name": "Brian",
        "gender": "Male",
        "accent": "US",
        "style": "Clear & Contemporary",
        "description": "A confident, approachable voice for long-form nonfiction and essays.",
        "recommended": False
    },
    {
        "id": "en-GB-LibbyNeural",
        "name": "Libby",
        "gender": "Female",
        "accent": "British",
        "style": "Lively & Clear",
        "description": "A crisp British voice with an upbeat, easy-to-follow tone.",
        "recommended": False
    },
    {
        "id": "en-AU-NatashaNeural",
        "name": "Natasha",
        "gender": "Female",
        "accent": "Australian",
        "style": "Easygoing & Warm",
        "description": "A relaxed Australian voice that keeps long listening sessions light.",
        "recommended": False
    },
    {
        "id": "en-IN-NeerjaNeural",
        "name": "Neerja",
        "gender": "Female",
        "accent": "Indian English",
        "style": "Calm & Precise",
        "description": "A composed, articulate voice with a clear Indian English accent.",
        "recommended": False
    }
]

# Only free, built-in synthesis is exposed by the application.  This endpoint
# is retained for the UI's free-engine information sheet.
TTS_MODELS_INFO = [
    {
        "provider": "Edge Neural Speech",
        "model": "Microsoft Edge Neural Voices",
        "price_per_1m_chars": "$0.00",
        "cost_summary": "Free to use — no account or API key",
        "api_key_required": False,
        "quality": "Natural neural narration",
        "pros": [
            "Every narrator in the library uses this free engine",
            "No credit card, subscription, or API key",
            "Choose from a growing set of English accents and styles"
        ],
        "cons": ["Requires active internet connection during synthesis"]
    }
]

