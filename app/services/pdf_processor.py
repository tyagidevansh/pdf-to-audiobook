import asyncio
import io
import re
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import pymupdf
import pytesseract
from PIL import Image

from app.config import DEFAULT_OCR_DPI
from app.services.text_cleaner import cleaner
from app.models.schemas import PageBlock, CleaningStats, ExtractResponse


class PDFProcessor:
    """
    Handles PDF ingestion, smart page analysis, OCR detection for scanned/photo pages,
    and coordinates with TextCleaner to produce clean audiobook narration.
    """

    def __init__(self, ocr_dpi: int = DEFAULT_OCR_DPI):
        self.ocr_dpi = ocr_dpi

    async def extract_and_clean(
        self,
        job_id: str,
        filename: str,
        pdf_path: Path,
        progress_callback: Optional[Callable[[int, str], Any]] = None,
        filter_headers_footers: bool = True,
        filter_citations: bool = True,
        filter_book_matter: bool = True,
        unwrap_paragraphs: bool = True,
    ) -> ExtractResponse:
        """
        Extracts content from PDF with automatic OCR fallback for scanned/photo pages,
        cleans noise, and calculates audiobook duration statistics.
        """
        loop = asyncio.get_running_loop()

        # Run extraction in worker thread so large PDFs don't block the async event loop
        raw_pages, ocr_count = await loop.run_in_executor(
            None, self._process_pdf_sync, pdf_path, progress_callback
        )

        total_pages = len(raw_pages)

        # Notify cleaning phase
        if progress_callback:
            progress_callback(90, "Applying smart audiobook layout cleaning...")

        # Clean document across pages
        cleaned_text, stats = cleaner.clean_document(
            raw_pages,
            filter_headers_footers=filter_headers_footers,
            filter_citations=filter_citations,
            filter_book_matter=filter_book_matter,
            unwrap_paragraphs=unwrap_paragraphs,
        )

        # Build page blocks for preview
        page_blocks: List[PageBlock] = []
        for p in raw_pages:
            combined_page_text = "\n\n".join(b["text"] for b in p.get("blocks", []))
            page_blocks.append(
                PageBlock(
                    page_number=p["page_number"],
                    is_ocr=p["is_ocr"],
                    text=combined_page_text,
                    char_count=len(combined_page_text),
                )
            )

        words = re.findall(r"\b\w+\b", cleaned_text)
        total_words = len(words)
        # Average audiobook pace is ~150 words per minute (2.5 words/sec)
        est_seconds = int(total_words / 2.5) if total_words > 0 else 0

        mins, secs = divmod(est_seconds, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            formatted_duration = f"{hours}h {mins}m {secs}s"
        elif mins > 0:
            formatted_duration = f"{mins}m {secs}s"
        else:
            formatted_duration = f"{secs}s"

        if progress_callback:
            progress_callback(100, "Text analysis complete.")

        return ExtractResponse(
            job_id=job_id,
            filename=filename,
            total_pages=total_pages,
            ocr_pages_count=ocr_count,
            total_words=total_words,
            estimated_duration_seconds=est_seconds,
            estimated_duration_formatted=formatted_duration,
            cleaned_text=cleaned_text,
            pages=page_blocks,
            stats=stats,
        )

    def _process_pdf_sync(
        self, pdf_path: Path, progress_callback: Optional[Callable[[int, str], Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        raw_pages: List[Dict[str, Any]] = []
        ocr_count = 0

        for idx, page in enumerate(doc):
            page_num = idx + 1
            pct = int((idx / total_pages) * 85)
            if progress_callback:
                progress_callback(pct, f"Inspecting page {page_num} of {total_pages}...")

            rect = page.rect
            h = rect.height
            # Asking PyMuPDF to sort gives a stable top-to-bottom reading order,
            # which is essential for headings, contents pages, and clean narration.
            blocks = page.get_text("blocks", sort=True)

            # Check if page has digital text blocks
            # block format: (x0, y0, x1, y1, text, block_no, block_type)
            text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
            total_chars = sum(len(b[4].strip()) for b in text_blocks)

            is_scanned = False
            # If text is extremely scarce (< 50 characters) or nonexistent, treat as scanned/photo page
            if len(text_blocks) == 0 or total_chars < 50:
                is_scanned = True
                ocr_count += 1
                if progress_callback:
                    progress_callback(pct, f"Running OCR on photo page {page_num}...")

                ocr_page_blocks = self._ocr_page(page)
                raw_pages.append(
                    {
                        "page_number": page_num,
                        "is_ocr": True,
                        "blocks": ocr_page_blocks,
                    }
                )
            else:
                # Digital text page
                page_extracted_blocks = []
                for b in text_blocks:
                    x0, y0, x1, y1, text, b_no, _ = b
                    text = text.strip()
                    if not text:
                        continue
                    is_top = y1 <= (h * 0.12)
                    is_bottom = y0 >= (h * 0.88)
                    page_extracted_blocks.append(
                        {
                            "text": text,
                            "bbox": (x0, y0, x1, y1),
                            "is_top": is_top,
                            "is_bottom": is_bottom,
                        }
                    )

                raw_pages.append(
                    {
                        "page_number": page_num,
                        "is_ocr": False,
                        "blocks": page_extracted_blocks,
                    }
                )

        doc.close()
        return raw_pages, ocr_count

    def _ocr_page(self, page: pymupdf.Page) -> List[Dict[str, Any]]:
        """Renders page at high DPI and runs OCR layout analysis."""
        pix = page.get_pixmap(dpi=self.ocr_dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        w, h = img.size

        # Use image_to_data to capture block positions
        try:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            blocks_dict: Dict[int, Dict[str, Any]] = {}
            n_boxes = len(data["text"])

            for i in range(n_boxes):
                word = data["text"][i].strip()
                if not word:
                    continue
                b_num = data["block_num"][i]
                top = data["top"][i]
                height = data["height"][i]
                bottom = top + height

                if b_num not in blocks_dict:
                    blocks_dict[b_num] = {
                        "words": [],
                        "top": top,
                        "bottom": bottom,
                    }
                blocks_dict[b_num]["words"].append(word)
                blocks_dict[b_num]["top"] = min(blocks_dict[b_num]["top"], top)
                blocks_dict[b_num]["bottom"] = max(blocks_dict[b_num]["bottom"], bottom)

            result_blocks: List[Dict[str, Any]] = []
            for b_num, info in sorted(blocks_dict.items(), key=lambda item: item[1]["top"]):
                text = " ".join(info["words"]).strip()
                if not text:
                    continue
                is_top = info["bottom"] <= (h * 0.12)
                is_bottom = info["top"] >= (h * 0.88)
                result_blocks.append(
                    {
                        "text": text,
                        "bbox": (0, info["top"], w, info["bottom"]),
                        "is_top": is_top,
                        "is_bottom": is_bottom,
                    }
                )

            if not result_blocks:
                # Fallback to direct string if bounding box grouping was empty
                full_str = pytesseract.image_to_string(img).strip()
                if full_str:
                    return [{"text": full_str, "bbox": (0, 0, w, h), "is_top": False, "is_bottom": False}]
            return result_blocks

        except Exception as e:
            # Fallback to basic string OCR if image_to_data fails
            full_str = pytesseract.image_to_string(img).strip()
            return [{"text": full_str, "bbox": (0, 0, w, h), "is_top": False, "is_bottom": False}] if full_str else []


pdf_processor = PDFProcessor()

