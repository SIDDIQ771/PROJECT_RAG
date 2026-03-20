import os
from vectorstore.chroma_client import get_chroma_client
from ingestion.pdf_loader import load_pdf
from ingestion.docx_loader import load_docx
from ingestion.text_loader import load_text
from config.settings import settings

db = get_chroma_client()


def process_shared_folder():
    folder = settings.SHARED_FOLDER_PATH
    print(f"[Shared Folder] Scanning: {folder}")

    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            process_single_file(path)


def process_single_file(path: str):
    ext = path.lower().split(".")[-1]

    if ext == "pdf":
        text = load_pdf(path)
    elif ext in ["docx", "doc"]:
        text = load_docx(path)
    elif ext in ["txt", "md"]:
        text = load_text(path)
    else:
        print(f"[Shared Folder] Skipping unsupported file: {path}")
        return

    metadata = {
        "source": f"Shared_Folder-{os.path.basename(path)}",
        "filename": os.path.basename(path),
        "path": path
    }

    db.add(
        documents=[text],
        metadatas=[metadata],
        ids=[f"doc-{os.path.basename(path)}"]
    )

    print(f"[Shared Folder] Stored: {os.path.basename(path)}")
