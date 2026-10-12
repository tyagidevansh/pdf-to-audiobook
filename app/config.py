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
    }
]

# TTS Model Comparison Guide
TTS_MODELS_INFO = [
    {
        "provider": "Edge-TTS (Active Built-in)",
        "model": "Microsoft Edge Neural Voices",
        "price_per_1m_chars": "$0.00",
        "cost_summary": "100% Free & Unlimited",
        "api_key_required": False,
        "quality": "Studio Neural (Audiobook Grade)",
        "pros": [
            "Completely free with no API key or credit card needed",
            "High quality natural human voices with novel/narrator intonations",
            "Instant conversion with zero cloud bill"
        ],
        "cons": ["Requires active internet connection during synthesis"]
    },
    {
        "provider": "Google Cloud Text-to-Speech",
        "model": "Journey & Neural2",
        "price_per_1m_chars": "$16.00",
        "cost_summary": "$16.00 / 1M chars (1,000,000 chars FREE / month)",
        "api_key_required": True,
        "quality": "Exceptional",
        "pros": [
            "Generous monthly free tier (1M chars free every month)",
            "Journey voices are among the most natural commercial voices",
            "Cheapest commercial tier after free quota"
        ],
        "cons": ["Requires Google Cloud Console setup and billing credit card"]
    },
    {
        "provider": "OpenAI Audio TTS",
        "model": "tts-1",
        "price_per_1m_chars": "$15.00",
        "cost_summary": "$0.015 / 1,000 chars (~$15.00 / 1M chars)",
        "api_key_required": True,
        "quality": "Very Good",
        "pros": [
            "Easy plug-and-play if you already have an OpenAI API key",
            "Voices like Onyx and Alloy have good cadence"
        ],
        "cons": ["No free tier; charges per character generated"]
    },
    {
        "provider": "Deepgram",
        "model": "Aura",
        "price_per_1m_chars": "$15.00",
        "cost_summary": "$0.015 / 1,000 chars (~$15.00 / 1M chars)",
        "api_key_required": True,
        "quality": "Very Good (Ultra-low latency)",
        "pros": ["Extremely fast streaming", "Good pricing parity with OpenAI"],
        "cons": ["Smaller voice catalog compared to Azure/Edge"]
    },
    {
        "provider": "ElevenLabs",
        "model": "Multilingual v2 / Flash",
        "price_per_1m_chars": "$150.00 - $300.00",
        "cost_summary": "$0.15 - $0.30 / 1,000 chars ($150 - $300 / 1M chars)",
        "api_key_required": True,
        "quality": "Industry Leading",
        "pros": ["Best-in-class emotional acting and voice cloning"],
        "cons": ["Expensive for full-length books (a 100k-word book can cost $75+)"]
    }
]

