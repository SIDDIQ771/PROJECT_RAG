import os
import re
import whisper
from ingestion.chunker import chunk_text
from vectorstore.chroma_client import get_chroma_client

db = get_chroma_client()

VIDEO_EXT      = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}
TRANSCRIPT_EXT = [".txt", ".vtt", ".srt"]

_whisper_model = None

def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("[Transcriber] Loading Whisper model...")
        _whisper_model = whisper.load_model("base")
        print("[Transcriber] Whisper model loaded.")
    return _whisper_model


def _clean_vtt(text: str) -> str:
    text = re.sub(r"WEBVTT.*?\n", "", text)
    text = re.sub(r"\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}", "", text)
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _clean_srt(text: str) -> str:
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _read_transcript_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if ext == ".vtt":
        return _clean_vtt(content)
    elif ext == ".srt":
        return _clean_srt(content)
    return content.strip()


def find_existing_transcript(video_path: str) -> str | None:
    base = os.path.splitext(video_path)[0]
    for ext in TRANSCRIPT_EXT:
        transcript_path = base + ext
        if os.path.exists(transcript_path):
            print(f"[Transcriber] Found existing transcript: {transcript_path}")
            return _read_transcript_file(transcript_path)
    return None


def generate_transcript(video_path: str) -> str:
    print(f"[Transcriber] Generating transcript for: {os.path.basename(video_path)}")
    model = _get_whisper_model()
    result = model.transcribe(video_path)
    transcript = result["text"].strip()

    # ✅ Print the transcribed text to console
    print(f"\n[Transcriber] --- Transcribed Text ---\n{transcript}\n[Transcriber] --- End of Transcript ---\n")

    transcript_path = os.path.splitext(video_path)[0] + ".txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"[Transcriber] Transcript saved: {transcript_path}")
    return transcript


def process_video(video_path: str):
    filename = os.path.basename(video_path)
    print(f"[Transcriber] Processing video: {filename}")

    transcript = find_existing_transcript(video_path)
    if transcript:
        # ✅ Also print existing transcript when loaded from file
        print(f"\n[Transcriber] --- Loaded Transcript ---\n{transcript}\n[Transcriber] --- End of Transcript ---\n")
    else:
        transcript = generate_transcript(video_path)

    if not transcript or not transcript.strip():
        print(f"[Transcriber] Empty transcript for {filename}, skipping.")
        return

    header = f"VIDEO: {filename}\nTRANSCRIPT:\n\n"
    full_text = header + transcript

    chunks = chunk_text(full_text)

    base_metadata = {
        "source":   f"VIDEO-{filename}",
        "filename": filename,
        "path":     video_path,
        "type":     "video_transcript",
    }

    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        if filename not in chunk:
            chunk = f"VIDEO: {filename}\n\n" + chunk
        documents.append(chunk)
        metadatas.append({**base_metadata, "chunk_index": i, "total_chunks": len(chunks)})
        ids.append(f"video-{filename}-chunk-{i}")

    db.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[Transcriber] Upserted {len(chunks)} chunks from {filename}")


def is_video_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in VIDEO_EXT