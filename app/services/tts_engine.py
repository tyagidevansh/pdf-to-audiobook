import asyncio
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Callable
import edge_tts

from app.config import AUDIO_DIR


class TTSProvider(ABC):
    """Abstract TTS provider interface for pluggable speech engines."""

    @abstractmethod
    async def synthesize(
        self,
        job_id: str,
        text: str,
        voice_id: str,
        speed: float,
        output_path: Path,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Path:
        pass


class EdgeTTSProvider(TTSProvider):
    """
    Microsoft Edge Neural TTS provider.
    100% Free, zero-API-key, studio neural voices tailored for audiobooks.
    """

    MAX_CHUNK_CHARS = 2000

    async def synthesize(
        self,
        job_id: str,
        text: str,
        voice_id: str,
        speed: float,
        output_path: Path,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Path:
        # Format rate string (e.g. 1.25x -> "+25%", 0.85x -> "-15%")
        rate_int = int(round((speed - 1.0) * 100))
        rate_str = f"{rate_int:+d}%"

        # Split text into logical chunks
        chunks = self._chunk_text(text, self.MAX_CHUNK_CHARS)
        total_chunks = len(chunks)

        if total_chunks == 0:
            raise ValueError("No text provided for audio synthesis.")

        temp_dir = AUDIO_DIR / f"temp_{job_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            if total_chunks == 1:
                # Single chunk: synthesize directly to target
                if progress_callback:
                    progress_callback(10, "Synthesizing audio stream...")
                comm = edge_tts.Communicate(chunks[0], voice_id, rate=rate_str)
                await comm.save(str(output_path))
                if progress_callback:
                    progress_callback(100, "Audio generation complete.")
                return output_path

            # Multi-chunk synthesis with concurrency limiter
            chunk_files: List[Path] = [temp_dir / f"chunk_{i:04d}.mp3" for i in range(total_chunks)]
            semaphore = asyncio.Semaphore(3)  # Maximum 3 concurrent streams
            completed_count = 0

            async def synth_one(idx: int, chunk_text: str, dest: Path):
                nonlocal completed_count
                async with semaphore:
                    comm = edge_tts.Communicate(chunk_text, voice_id, rate=rate_str)
                    await comm.save(str(dest))
                    completed_count += 1
                    pct = int(10 + (completed_count / total_chunks) * 80)
                    if progress_callback:
                        progress_callback(
                            pct,
                            f"Synthesizing section {completed_count} of {total_chunks}..."
                        )

            tasks = [
                synth_one(i, chunk, chunk_files[i])
                for i, chunk in enumerate(chunks)
            ]
            await asyncio.gather(*tasks)

            # Concat chunks using ffmpeg
            if progress_callback:
                progress_callback(92, "Assembling complete audiobook...")

            await self._concat_chunks(chunk_files, output_path)

            if progress_callback:
                progress_callback(100, "Audiobook ready.")

            return output_path

        finally:
            # Clean up temp chunk files
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _chunk_text(self, text: str, max_chars: int) -> List[str]:
        """
        Splits text into chunks <= max_chars while preserving
        paragraph and sentence boundaries.
        """
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(para) > max_chars:
                # Paragraph itself exceeds max_chars; split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current_chunk) + len(sentence) + 1 <= max_chars:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
            else:
                if len(current_chunk) + len(para) + 2 <= max_chars:
                    if current_chunk:
                        current_chunk = f"{current_chunk}\n\n{para}"
                    else:
                        current_chunk = para
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def _concat_chunks(self, chunk_files: List[Path], output_path: Path):
        """Losslessly concatenates MP3 audio chunks into a unified MP3 using FFmpeg."""
        concat_list_file = chunk_files[0].parent / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for c_file in chunk_files:
                f.write(f"file '{c_file.resolve()}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(output_path),
        ]

        loop = asyncio.get_running_loop()
        proc = await loop.run_in_executor(
            None,
            lambda: subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        )
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"FFmpeg concatenation failed: {err}")


tts_engine = EdgeTTSProvider()

