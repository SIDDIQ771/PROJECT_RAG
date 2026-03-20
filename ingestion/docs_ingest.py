import os
from ingestion.chunker import chunk_text
from ingestion.pdf_loader import load_pdf
from ingestion.docx_loader import load_docx
from config.settings import settings
from vectorstore.chroma_client import get_chroma_client

db = get_chroma_client()


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
    print(f"[Docs] Processing file: {file_path}")
    text = load_document_text(file_path)
    if not text.strip():
        print(f"[Docs] Skipped empty or unsupported file: {file_path}")
        return

    filename = os.path.basename(file_path)

    # ✅ Use optimized chunker
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