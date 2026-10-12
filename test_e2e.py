import asyncio
from pathlib import Path
from app.services.pdf_processor import pdf_processor
from app.services.tts_engine import tts_engine
from app.config import CURATED_VOICES, TTS_MODELS_INFO, AUDIO_DIR

async def run_all_tests():
    print("========================================")
    print("RUNNING END-TO-END VERIFICATION TESTS")
    print("========================================")

    # 1. Config tests
    print("\n[1] Checking Curated Voices & Models...")
    assert len(CURATED_VOICES) >= 5, "Should have at least 5 curated voices"
    assert len(TTS_MODELS_INFO) >= 4, "Should have model cost breakdown"
    print(f"✓ {len(CURATED_VOICES)} curated voices available.")
    print(f"✓ {len(TTS_MODELS_INFO)} TTS engine cost profiles configured.")

    # 2. Digital PDF extraction & Smart Cleaning
    print("\n[2] Testing Digital PDF Extraction & Smart Cleaning...")
    digital_path = Path("sample_pdfs/sample_digital.pdf")
    res1 = await pdf_processor.extract_and_clean(
        job_id="test_e2e_digital",
        filename="sample_digital.pdf",
        pdf_path=digital_path,
        filter_headers_footers=True,
        filter_citations=True,
        unwrap_paragraphs=True,
    )
    print(f"✓ Total pages: {res1.total_pages}")
    print(f"✓ OCR pages: {res1.ocr_pages_count} (Expected 0 for digital)")
    print(f"✓ Headers removed: {res1.stats.headers_removed}")
    print(f"✓ Footers removed: {res1.stats.footers_removed}")
    print(f"✓ Hyphens fixed: {res1.stats.hyphens_fixed}")
    print(f"✓ Word count: {res1.total_words}")
    assert res1.ocr_pages_count == 0
    assert res1.stats.headers_removed >= 1
    assert "THE CHRONICLES OF TOMORROW" not in res1.cleaned_text, "Running header should be excluded!"
    assert "Page 1" not in res1.cleaned_text, "Page number footer should be excluded!"
    assert "tempestuous" in res1.cleaned_text, "Hyphenated 'tempestu- ous' should be cleanly joined!"

    # 3. Scanned / Photo PDF OCR Extraction
    print("\n[3] Testing Scanned/Photo PDF OCR Extraction...")
    scanned_path = Path("sample_pdfs/sample_scanned.pdf")
    res2 = await pdf_processor.extract_and_clean(
        job_id="test_e2e_scanned",
        filename="sample_scanned.pdf",
        pdf_path=scanned_path,
        filter_headers_footers=True,
        filter_citations=True,
        unwrap_paragraphs=True,
    )
    print(f"✓ Scanned pages: {res2.total_pages}")
    print(f"✓ OCR pages detected: {res2.ocr_pages_count} (Expected 1)")
    print(f"✓ Extracted text length: {len(res2.cleaned_text)} characters")
    assert res2.ocr_pages_count == 1, "Should have triggered OCR on scanned page"
    assert "mountain" in res2.cleaned_text.lower() or "traveler" in res2.cleaned_text.lower()
    print("✓ Scanned page OCR extracted text successfully!")

    # 4. Audio Generation test
    print("\n[4] Testing Audio Generation Pipeline with Edge-TTS...")
    audio_output = AUDIO_DIR / "test_e2e_digital.mp3"
    await tts_engine.synthesize(
        job_id="test_e2e_digital",
        text=res1.cleaned_text[:400], # Test first couple paragraphs
        voice_id="en-US-AriaNeural",
        speed=1.0,
        output_path=audio_output,
        progress_callback=lambda p, m: print(f"  Synthesis progress: {p}% - {m}")
    )
    assert audio_output.exists(), "Generated audio file must exist"
    size_kb = audio_output.stat().st_size / 1024
    print(f"✓ Generated audio file: {audio_output} ({size_kb:.1f} KB)")
    assert size_kb > 5, "Audio file should be non-trivial size"

    print("\n========================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_all_tests())

