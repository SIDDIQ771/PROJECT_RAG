import os
from ingestion.chunker import chunk_text
from ingestion.pdf_loader import load_pdf
from ingestion.docx_loader import load_docx
from config.settings import settings
from vectorstore.chroma_client import get_chroma_client

db = get_chroma_client()

SUPPORTED_VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}
SUPPORTED_DOC_EXT   = {".pdf", ".docx", ".md"}

# ✅ Ignore transcript files saved by video_transcriber — they are already
# ingested as VIDEO- chunks and must not be re-ingested as DOC- chunks
IGNORED_FILES = {"KT_Recording_testdata.txt"}  # auto-populated at runtime


def _is_transcript_file(file_path: str) -> bool:
    """Skip .txt files that are auto-generated transcripts alongside videos."""
    if not file_path.endswith(".txt"):
        return False
    # If a video with same base name exists, this is a transcript file
    base = os.path.splitext(file_path)[0]
    for ext in SUPPORTED_VIDEO_EXT:
        if os.path.exists(base + ext):
            return True
    return False


def load_document_text(file_path: str) -> str:
    ext = file_path.lower()
    if ext.endswith(".pdf"):
        return load_pdf(file_path)
    if ext.endswith(".docx"):
        return load_docx(file_path)
    if ext.endswith(".txt") or ext.endswith(".md"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def process_single_document(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()

    # Route video files to video transcriber
    if ext in SUPPORTED_VIDEO_EXT:
        from ingestion.video_transcriber import process_video
        process_video(file_path)
        return

    # ✅ Skip auto-generated transcript .txt files
    if _is_transcript_file(file_path):
        print(f"[Docs] Skipping transcript file (already ingested as video): {os.path.basename(file_path)}")
        return

    if ext not in SUPPORTED_DOC_EXT and ext != ".txt":
        print(f"[Docs] Skipping unsupported file type: {file_path}")
        return

    print(f"[Docs] Processing file: {file_path}")
    text = load_document_text(file_path)
    if not text.strip():
        print(f"[Docs] Skipped empty or unsupported file: {file_path}")
        return

    filename = os.path.basename(file_path)
    chunks = chunk_text(text)

    base_metadata = {
        "source":   f"DOC-{filename}",
        "filename": filename,
        "path":     file_path,
    }

    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append({**base_metadata, "chunk_index": i, "total_chunks": len(chunks)})
        ids.append(f"doc-{filename}-chunk-{i}")

    db.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"[Docs] Upserted {len(chunks)} chunks from {filename}")


def process_documents():
    folder = settings.SHARED_FOLDER_PATH
    if not os.path.exists(folder):
        print(f"[Docs] ⚠️  Shared folder not found: {folder}")
        return
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    print(f"[Docs] Found {len(files)} files in {folder}")
    for filename in files:
        path = os.path.join(folder, filename)
        process_single_document(path)