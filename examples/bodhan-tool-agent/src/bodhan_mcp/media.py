"""Deterministic media plumbing: ffmpeg and PyMuPDF only, no models.

Everything here is plain code on purpose. Inspecting a file, splitting audio on
silence, rendering PDF pages and concatenating audio are all jobs an LLM would
do worse, slower and more expensively than a subprocess call.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus", ".aac", ".wma"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
TEXT_SUFFIXES = {".txt", ".md", ".srt", ".vtt", ".json"}
DOC_SUFFIXES = {".pdf"}


class MediaError(RuntimeError):
    """Raised for unreadable or unsupported media, with an actionable message."""


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def require_ffmpeg() -> None:
    if not ffmpeg_available():
        raise MediaError(
            "ffmpeg and ffprobe are required but were not found on PATH. "
            "Install ffmpeg (https://ffmpeg.org/download.html) and retry."
        )


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise MediaError(f"{cmd[0]} failed: {proc.stderr.strip()[:400]}")
    return proc


def kind_of(path: str | Path) -> str:
    """Classify a file by extension: audio, video, image, document, text or unknown."""
    suffix = Path(path).suffix.lower()
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in DOC_SUFFIXES:
        return "document"
    if suffix in TEXT_SUFFIXES:
        return "text"
    return "unknown"


@dataclass
class MediaInfo:
    path: str
    kind: str
    size_bytes: int
    duration_seconds: float | None = None
    page_count: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    has_audio_stream: bool | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def probe(path: str | Path) -> MediaInfo:
    """Inspect a file without calling any model. Free."""
    p = Path(path)
    if not p.exists():
        raise MediaError(f"File not found: {p}")
    kind = kind_of(p)
    info = MediaInfo(path=str(p), kind=kind, size_bytes=p.stat().st_size)

    if kind in {"audio", "video"}:
        require_ffmpeg()
        out = _run([
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(p),
        ]).stdout
        data = json.loads(out)
        fmt = data.get("format", {})
        if "duration" in fmt:
            info.duration_seconds = round(float(fmt["duration"]), 3)
        audio_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
        info.has_audio_stream = bool(audio_streams)
        if audio_streams:
            first = audio_streams[0]
            if "sample_rate" in first:
                info.sample_rate = int(first["sample_rate"])
            if "channels" in first:
                info.channels = int(first["channels"])

    elif kind == "document":
        import fitz  # PyMuPDF

        with fitz.open(str(p)) as doc:
            info.page_count = doc.page_count

    elif kind == "image":
        info.page_count = 1

    return info


def extract_audio(path: str | Path, out_path: str | Path, sample_rate: int = 16_000) -> Path:
    """Pull a mono 16 kHz WAV out of any audio or video container."""
    require_ffmpeg()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-i", str(path),
        "-vn", "-ac", "1", "-ar", str(sample_rate),
        "-c:a", "pcm_s16le", str(out),
    ])
    return out


def split_audio(path: str | Path, window_seconds: float, out_dir: str | Path,
                overlap_seconds: float = 0.0) -> list[tuple[Path, float, float]]:
    """Split audio into fixed windows, returning (path, start, end) for each.

    Indic-Transcribe accepts up to 30 seconds per call, so anything longer has to
    be windowed. A small overlap stops a word being lost exactly on a boundary.
    """
    require_ffmpeg()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    info = probe(path)
    total = info.duration_seconds or 0.0
    if total <= 0:
        raise MediaError(f"Could not determine duration of {path}")

    chunks: list[tuple[Path, float, float]] = []
    step = max(0.1, window_seconds - overlap_seconds)
    start = 0.0
    index = 0
    while start < total:
        end = min(start + window_seconds, total)
        chunk_path = out_dir / f"chunk_{index:04d}.wav"
        _run([
            "ffmpeg", "-y", "-i", str(path),
            "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
            str(chunk_path),
        ])
        chunks.append((chunk_path, round(start, 3), round(end, 3)))
        index += 1
        if end >= total:
            break
        start += step
    return chunks


def concat_audio(parts: list[str | Path], out_path: str | Path) -> Path:
    """Concatenate audio files in order into one track."""
    require_ffmpeg()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not parts:
        raise MediaError("concat_audio called with no parts")
    if len(parts) == 1:
        shutil.copyfile(parts[0], out)
        return out

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        for part in parts:
            escaped = str(Path(part).resolve()).replace("'", r"'\''")
            fh.write(f"file '{escaped}'\n")
        list_file = fh.name
    try:
        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
              "-c:a", "libmp3lame", "-q:a", "2", str(out)])
    finally:
        Path(list_file).unlink(missing_ok=True)
    return out


def normalize_loudness(path: str | Path, out_path: str | Path, target_lufs: float = -16.0) -> Path:
    """Normalise speech loudness to a broadcast-style target."""
    require_ffmpeg()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-i", str(path),
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
        str(out),
    ])
    return out


def pdf_to_images(path: str | Path, out_dir: str | Path, dpi: int = 300,
                  pages: list[int] | None = None) -> list[Path]:
    """Render PDF pages to PNGs.

    Deliberately renders to image rather than reading any embedded text layer --
    all text must come from Indic-OCR.
    """
    import fitz  # PyMuPDF

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(str(path)) as doc:
        wanted = pages if pages else range(1, doc.page_count + 1)
        for page_no in wanted:
            if page_no < 1 or page_no > doc.page_count:
                raise MediaError(
                    f"Page {page_no} is out of range: {path} has {doc.page_count} pages."
                )
            page = doc.load_page(page_no - 1)
            pix = page.get_pixmap(matrix=matrix)
            target = out_dir / f"page_{page_no:03d}.png"
            pix.save(str(target))
            rendered.append(target)
    return rendered


def split_sentences(text: str, max_chars: int) -> list[str]:
    """Split text into pieces no longer than max_chars, preferring sentence ends.

    Used to keep Indic-Speak inputs short without cutting mid-sentence, which is
    what makes synthesised speech sound clipped.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    terminators = "।?!.\n"
    pieces: list[str] = []
    current = ""
    buffer = ""
    for ch in text:
        buffer += ch
        if ch in terminators:
            if len(current) + len(buffer) <= max_chars:
                current += buffer
            else:
                if current:
                    pieces.append(current.strip())
                current = buffer
            buffer = ""
    current += buffer
    if current.strip():
        pieces.append(current.strip())

    # Any single sentence longer than the limit still has to be broken on words.
    final: list[str] = []
    for piece in pieces:
        if len(piece) <= max_chars:
            final.append(piece)
            continue
        words = piece.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > max_chars:
                if line:
                    final.append(line.strip())
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            final.append(line.strip())
    return [p for p in final if p]
