# Audion — Smart PDF to Audiobook Studio

An intelligent proof-of-concept web application that converts **any PDF** (including scanned documents and photographed pages) into natural, studio-quality audiobooks.

---

## Highlights & Capabilities

- **Works with Any PDF**:
  - Automatically identifies whether each page contains digital text or is a scanned photograph / raster image.
  - Automatically executes high-resolution OCR (Tesseract layout analysis at 200 DPI) for photo pages with zero manual configuration.
- **Smart Audiobook Filter (Knows what to read and what NOT to read)**:
  - **Running Header & Footer Suppression**: Detects repeating book titles, chapter headers, copyright marks across pages and excludes them from speech.
  - **Page Number Removal**: Filters out standalone page numbers (e.g. `42`, `- 13 -`, `Page 5 of 80`).
  - **Footnote & Citation Filtering**: Cleans out bracketed citations `[1]`, `[1-3]`, and bottom footnote annotations so narrator flow isn't disrupted.
  - **Hyphenation Repair**: Automatically welds broken words across linebreaks (`tempestu- \n ous` &rarr; `tempestuous`).
  - **Paragraph Flow Reconstruction**: Unwraps hard line breaks while respecting true paragraph indents and section headings.
  - **Interactive Script Inspector**: Users can view the cleaned text, see noise reduction audit stats, and make tweaks before generating audio.
- **100% Free Studio-Grade Voice Synthesis**:
  - Built-in integration with **Microsoft Edge Neural Speech** (`edge-tts`).
  - Zero API key required, zero monthly cloud bill, unlimited generation.
  - Curated narrator voices tailored specifically for audiobooks (Aria, Guy, Christopher, Jenny, Ryan, Sonia).
  - Includes narration speed control (0.8x to 1.5x) and a voice sample preview feature.
- **Clean, Luxury Dark UI**:
  - Modern, responsive interface with drag-and-drop file upload.
  - Real-time Server-Sent Events (SSE) progress tracking.
  - Built-in audiobook player with waveform scrubber, 10-second skip buttons, playback speed multiplier, and one-click `.mp3` download.
- **Modular Architecture for Future Expansion**:
  - Abstract storage interface (`StorageProvider`) currently storing locally, ready for single-line swap to AWS S3, Cloudflare R2, or Supabase.
  - Clean API structure ready for user accounts and remote storage when you scale past the POC stage.

---

## TTS Engine & Cost Comparison

| Engine / Provider | Model | Cost per 1M Characters | API Key Required | Quality / Best Use Case |
|---|---|---|---|---|
| **Edge-TTS (Active Built-in)** | Microsoft Edge Neural Voices | **$0.00 (100% Free)** | **No** | **Studio Neural Quality**. Best for free, high-fidelity audiobooks. |
| **Google Cloud TTS** | Journey & Neural2 | **$16.00 / 1M chars** (1,000,000 chars/mo **FREE**) | Yes | Exceptional realism. Very cost-effective with free tier. |
| **OpenAI Audio TTS** | `tts-1` | **$15.00 / 1M chars** ($0.015 / 1k chars) | Yes | Good cadence, simple REST API. |
| **Deepgram** | Aura | **$15.00 / 1M chars** ($0.015 / 1k chars) | Yes | Ultra-low latency conversational voices. |
| **ElevenLabs** | Multilingual v2 | **$150.00 – $300.00 / 1M chars** | Yes | Elite emotional acting, but expensive for book-length audio. |

---

## Quick Start

### 1. Requirements
- Python 3.10+
- `tesseract` (for OCR on scanned/photo pages)
- `ffmpeg` (for lossless audio chunk concatenation)

*(Both `tesseract` and `ffmpeg` are already installed and verified on this system).*

### 2. Run the Server
Simply execute:
```bash
./run.sh
```
Or run directly via python:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## Project Structure

```
pdf-to-audiobook/
├── app/
│   ├── config.py             # App settings, curated voices, TTS model cost guide
│   ├── main.py               # FastAPI application & REST endpoints
│   ├── models/
│   │   └── schemas.py        # Pydantic data models & request/response schemas
│   └── services/
│       ├── storage.py        # Storage abstraction (Local & future S3/R2)
│       ├── pdf_processor.py  # PyMuPDF ingestion & Tesseract OCR fallback
│       ├── text_cleaner.py   # Multi-pass noise, header, footer & citation filter
│       ├── tts_engine.py     # Edge-TTS pipeline, chunking & FFmpeg concat
│       └── job_manager.py    # Background task tracking & SSE streaming
├── static/
│   ├── index.html            # Luxury dark UI with Tailwind & Lucide icons
│   ├── css/style.css         # Custom animations & styled sliders
│   └── js/app.js             # Client application logic & player controls
├── sample_pdfs/              # Test samples (digital book & scanned photo)
├── test_e2e.py               # Automated end-to-end test suite
├── requirements.txt          # Python dependencies
├── run.sh                    # One-click startup script
└── README.md
```

---

## Future Roadmap (Moving Beyond Proof-of-Concept)

1. **Remote Storage Migration**:
   - In `app/services/storage.py`, inherit from `StorageProvider` and implement `S3StorageProvider` (or Cloudflare R2 / Supabase Storage).
2. **User Authentication & Remote Library**:
   - Add user authentication (e.g. Supabase Auth, Clerk, or JWT OAuth).
   - Associate `job_id` with `user_id` so generated audiobooks persist in a remote personal library accessible across devices.
3. **Dedicated Audiobook Player**:
   - Chapter bookmarks, background audio playback on mobile browsers, sleep timer, and synchronized reading highlighting.

