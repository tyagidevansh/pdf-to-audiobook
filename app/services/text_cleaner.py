import re
from typing import List, Dict, Any, Tuple
from app.models.schemas import CleaningStats


class TextCleaner:
    """
    Intelligent document cleaner that filters out non-narrative elements
    so the speech synthesizer reads only genuine audiobook content.
    """

    # Regex patterns for page numbers
    PAGE_NUMBER_PATTERNS = [
        re.compile(r"^\s*(?:page\s*)?[-–—]?\s*\d+\s*[-–—]?(?:\s*(?:of|/)\s*\d+)?\s*$", re.IGNORECASE),
        re.compile(r"^\s*[-–—]\s*\d+\s*[-–—]\s*$", re.IGNORECASE),
        re.compile(r"^\s*(?:page\s*)?[ivxlcdm]+\s*$", re.IGNORECASE),
    ]

    # Citation markers like [1], [1, 2], [1-3], [12]
    CITATION_PATTERN = re.compile(r"\[\s*\d+(?:\s*[,-–—]\s*\d+)*\s*\]")

    # Parenthetical academic citations like (Smith, 2020) or (Johnson et al., 2019, p. 45)
    ACADEMIC_CITATION_PATTERN = re.compile(
        r"\([A-Z][a-zA-Z\s]+(?:et al\.?)?,?\s*(?:19|20)\d{2}(?:,\s*pp?\.?\s*\d+(?:-\d+)?)?\)"
    )

    # Footnote indicator at start of paragraph (e.g. "1. See also...", "* Notes on...")
    FOOTNOTE_START_PATTERN = re.compile(r"^(?:[\d*†‡§#]{1,3}\.?\s*|\[\d+\]\s*)")

    # Hyphenated words broken across line wraps (e.g. "infor- \n mation" -> "information")
    HYPHENATION_PATTERN = re.compile(r"(\b[a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,}\b)")

    # Common publisher / document noise patterns
    NOISE_PATTERNS = [
        re.compile(r"^(?:isbn|issn|doi):\s*[\d\-xX.]+", re.IGNORECASE),
        re.compile(r"^(?:https?://|www\.)\S+", re.IGNORECASE),
        re.compile(r"^(?:all rights reserved|printed in|copyright ©|©\s*\d{4})", re.IGNORECASE),
        re.compile(r"^[-=_*~]{3,}$"),  # Horizontal divider rules
    ]

    # Chapter / Section heading patterns. Introduction and preface deliberately
    # do not appear here: they are treated as optional front matter by default.
    CHAPTER_HEADING_PATTERN = re.compile(
        r"^(?:chapter\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)|"
        r"part\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five)|book\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five)|prologue|epilogue)\b",
        re.IGNORECASE
    )

    FRONT_MATTER_HEADING_PATTERN = re.compile(
        r"^(?:table\s+of\s+contents|contents|copyright|dedication|epigraph|foreword|"
        r"preface|introduction|acknowledg(?:e)?ments?|list\s+of\s+(?:illustrations|figures|tables)|"
        r"publication\s+(?:information|data)|title\s+page)\b",
        re.IGNORECASE,
    )
    BACK_MATTER_HEADING_PATTERN = re.compile(
        r"^(?:about\s+(?:the\s+)?author|also\s+by|other\s+books\s+by|bibliography|"
        r"references|index|endnotes?|notes|glossary|further\s+reading|permissions)\b",
        re.IGNORECASE,
    )
    LEGAL_PAGE_PATTERN = re.compile(
        r"\b(?:copyright|all rights reserved|library of congress|isbn|printed in|"
        r"published by|no part of this (?:book|publication))\b",
        re.IGNORECASE,
    )
    CONTENTS_ENTRY_PATTERN = re.compile(r"(?:\.{2,}|…{2,})\s*\d+\s*$|\s\d{1,4}\s*$")

    def clean_document(
        self,
        raw_pages: List[Dict[str, Any]],
        filter_headers_footers: bool = True,
        filter_citations: bool = True,
        filter_book_matter: bool = True,
        unwrap_paragraphs: bool = True,
    ) -> Tuple[str, CleaningStats]:
        """
        Processes all pages together to detect cross-page patterns
        (like repeated running headers) and produce seamless narrative text.
        """
        stats = CleaningStats()

        if not raw_pages:
            return "", stats

        # Step 1: Detect cross-page recurring headers and footers
        recurring_headers, recurring_footers = self._detect_recurring_margin_text(raw_pages)

        cleaned_page_texts: List[str] = []

        for page in raw_pages:
            blocks = page.get("blocks", [])
            page_text_lines: List[str] = []

            for block in blocks:
                block_text = block.get("text", "").strip()
                if not block_text:
                    continue

                is_top = block.get("is_top", False)
                is_bottom = block.get("is_bottom", False)

                # Check if block is a running header
                if filter_headers_footers and is_top:
                    norm = self._normalize_line(block_text)
                    if norm in recurring_headers:
                        stats.headers_removed += 1
                        continue

                # Check if block is a running footer or page number
                if filter_headers_footers and is_bottom:
                    norm = self._normalize_line(block_text)
                    if norm in recurring_footers:
                        stats.footers_removed += 1
                        continue
                    if self._is_page_number(block_text):
                        stats.page_numbers_removed += 1
                        continue

                # Check for standalone page number anywhere near edges
                if (is_top or is_bottom) and self._is_page_number(block_text):
                    stats.page_numbers_removed += 1
                    continue

                # Check if bottom block looks like a footnote
                if is_bottom and self._is_likely_footnote(block_text):
                    stats.footers_removed += 1
                    continue

                # Check for noise lines (ISBN, URLs, copyright marks)
                if any(p.search(block_text) for p in self.NOISE_PATTERNS):
                    continue

                page_text_lines.append(block_text)

            # Combine page blocks with clean paragraph breaks
            page_combined = "\n\n".join(page_text_lines)
            cleaned_page_texts.append(page_combined)

        # A book's title page, contents, foreword, legal notices and index are
        # usually valid text, so line-level noise filters cannot remove them.
        # Detect their page-level structure before merging the narration.
        if filter_book_matter:
            cleaned_page_texts = self._remove_book_matter(cleaned_page_texts, stats)

        # Step 2: Merge full text across pages
        full_text = "\n\n".join(cleaned_page_texts)

        # Step 3: Fix hyphenation broken across linebreaks
        def unhyphen(match):
            stats.hyphens_fixed += 1
            return match.group(1) + match.group(2)

        full_text = self.HYPHENATION_PATTERN.sub(unhyphen, full_text)

        # Step 4: Remove inline citations if requested
        if filter_citations:
            citations_found = len(self.CITATION_PATTERN.findall(full_text))
            stats.citations_removed += citations_found
            full_text = self.CITATION_PATTERN.sub("", full_text)
            full_text = self.ACADEMIC_CITATION_PATTERN.sub("", full_text)

        # Step 5: Clean OCR artifacts and normalize whitespace & typography
        full_text = self._normalize_typography(full_text)

        # Step 6: Unwrap soft line breaks within paragraphs
        if unwrap_paragraphs:
            full_text = self._unwrap_paragraphs(full_text)
            stats.paragraphs_formatted = len(full_text.split("\n\n"))

        # Step 7: Final cleanup: remove excessive blank lines
        full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()

        return full_text, stats

    def _remove_book_matter(
        self, page_texts: List[str], stats: CleaningStats
    ) -> List[str]:
        """Remove clearly non-narrative book pages without guessing at body text.

        If a real chapter/prologue marker occurs after recognised front matter,
        everything before that marker is safely considered book setup. For books
        without conventional chapter headings we only remove explicitly labelled
        pages, avoiding the risk of discarding the opening of the story.
        """
        first_anchor = next(
            (i for i, text in enumerate(page_texts) if self._is_narrative_anchor(text)),
            None,
        )
        has_recognised_front_matter = (
            first_anchor is not None
            and any(self._is_front_matter_page(text) for text in page_texts[:first_anchor])
        )

        retained: List[str] = []
        for index, text in enumerate(page_texts):
            if not text.strip():
                continue

            is_explicit_matter = (
                self._is_front_matter_page(text)
                or self._is_back_matter_page(text)
                or self._is_contents_page(text)
                or self._is_legal_page(text)
            )
            is_leading_book_setup = (
                has_recognised_front_matter
                and first_anchor is not None
                and index < first_anchor
            )

            if is_explicit_matter or is_leading_book_setup:
                stats.book_matter_pages_removed += 1
                continue
            retained.append(text)

        return retained

    def _first_meaningful_line(self, text: str) -> str:
        return next(iter(self._leading_lines(text)), "")

    def _leading_lines(self, text: str, limit: int = 8) -> List[str]:
        """Return early non-empty lines; PDF blocks may put a title before a heading."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines[:limit]

    def _is_front_matter_page(self, text: str) -> bool:
        return any(self.FRONT_MATTER_HEADING_PATTERN.match(line) for line in self._leading_lines(text))

    def _is_back_matter_page(self, text: str) -> bool:
        return any(self.BACK_MATTER_HEADING_PATTERN.match(line) for line in self._leading_lines(text))

    def _is_legal_page(self, text: str) -> bool:
        # Copyright language can be long, but a prose chapter should not contain
        # several publication markers packed together.
        return len(text.split()) < 550 and len(self.LEGAL_PAGE_PATTERN.findall(text)) >= 2

    def _is_contents_page(self, text: str) -> bool:
        if any(
            re.match(r"^(?:table\s+of\s+)?contents\b", line, re.IGNORECASE)
            for line in self._leading_lines(text)
        ):
            return True
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        entry_lines = sum(bool(self.CONTENTS_ENTRY_PATTERN.search(line)) for line in lines)
        return len(lines) >= 4 and entry_lines >= 3

    def _is_narrative_anchor(self, text: str) -> bool:
        leading_lines = self._leading_lines(text)
        if any(self.CHAPTER_HEADING_PATTERN.match(line) for line in leading_lines):
            return True
        # Common minimalist chapter styles: a standalone numeral followed by
        # prose, or a numeral and title on the same first line.
        return any(
            re.match(r"^(?:\d+|[ivxlcdm]+)(?:\s*[.:—-]\s*|\s*$)", line, re.IGNORECASE)
            for line in leading_lines
        )

    def _detect_recurring_margin_text(
        self, pages: List[Dict[str, Any]]
    ) -> Tuple[set, set]:
        """Identifies text snippets appearing repeatedly at the top or bottom of pages."""
        header_counts: Dict[str, int] = {}
        footer_counts: Dict[str, int] = {}

        total_pages = len(pages)
        if total_pages < 2:
            return set(), set()

        for page in pages:
            for block in page.get("blocks", []):
                text = self._normalize_line(block.get("text", ""))
                if not text or len(text) < 3:
                    continue

                if block.get("is_top", False):
                    header_counts[text] = header_counts.get(text, 0) + 1
                elif block.get("is_bottom", False):
                    footer_counts[text] = footer_counts.get(text, 0) + 1

        # A header/footer is recurring if it appears on >= 2 pages (or >= 25% of pages for longer docs)
        threshold = 2 if total_pages <= 4 else max(2, total_pages // 4)
        recurring_headers = {k for k, v in header_counts.items() if v >= threshold}
        recurring_footers = {k for k, v in footer_counts.items() if v >= threshold}

        return recurring_headers, recurring_footers

    def _is_page_number(self, text: str) -> bool:
        """Determines if a string is solely a page number."""
        text = text.strip()
        for pat in self.PAGE_NUMBER_PATTERNS:
            if pat.match(text):
                return True
        return False

    def _is_likely_footnote(self, text: str) -> bool:
        """Identifies text at the bottom of a page that is a footnote."""
        first_line = text.split("\n")[0].strip()
        return bool(self.FOOTNOTE_START_PATTERN.match(first_line))

    def _normalize_line(self, text: str) -> str:
        """Normalizes a string for fuzzy equality check."""
        t = re.sub(r"\d+", "", text).lower().strip()
        t = re.sub(r"[^\w\s]", "", t)
        return re.sub(r"\s+", " ", t)

    def _normalize_typography(self, text: str) -> str:
        """Normalizes unicode quotes, OCR dashes, ligatures, and symbols."""
        replacements = [
            ("“", '"'),
            ("”", '"'),
            ("‘", "'"),
            ("’", "'"),
            ("—", " — "),
            ("–", " - "),
            ("…", "..."),
            ("ﬁ", "fi"),
            ("ﬂ", "fl"),
            ("ﬀ", "ff"),
            ("ffi", "ffi"),
            ("ffl", "ffl"),
            ("\r\n", "\n"),
            ("\r", "\n"),
        ]
        for src, dest in replacements:
            text = text.replace(src, dest)

        # Remove lone OCR noise characters on their own line like '~', '|', '_'
        text = re.sub(r"^\s*[_|~•·]\s*$", "", text, flags=re.MULTILINE)

        # Normalize multiple spaces into single space (except newlines)
        text = re.sub(r"[ \t]+", " ", text)
        return text

    def _unwrap_paragraphs(self, text: str) -> str:
        """
        Converts hard-wrapped PDF lines into fluid flowing paragraphs.
        Preserves double newlines (paragraph boundaries) and headings.
        """
        # Split into distinct blocks by 2 or more newlines
        raw_paragraphs = re.split(r"\n\s*\n", text)
        cleaned_paragraphs: List[str] = []

        for para in raw_paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if this paragraph is a chapter/section heading
            if self.CHAPTER_HEADING_PATTERN.match(para) or (len(para) < 60 and para.isupper()):
                # Keep heading distinct with clear pause
                cleaned_paragraphs.append(para)
                continue

            # Join lines inside the paragraph with a single space
            lines = [line.strip() for line in para.split("\n") if line.strip()]
            joined = " ".join(lines)
            cleaned_paragraphs.append(joined)

        return "\n\n".join(cleaned_paragraphs)


cleaner = TextCleaner()

