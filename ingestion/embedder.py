# embedder.py — now a thin wrapper around chroma_client
# All embedding is handled by the SentenceTransformer in chroma_client.py
# so we just call db.upsert() directly — no separate embedding step needed.

from vectorstore.chroma_client import get_chroma_client

db = get_chroma_client()

def embed_and_store(chunks: list[str], metadata: dict):
    """Store chunks into ChromaDB — embeddings handled automatically by collection."""
    ids = [f"{metadata['source']}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{**metadata, "chunk_id": i} for i in range(len(chunks))]

    db.upsert(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    print(f"[Embedder] Stored {len(chunks)} chunks from {metadata['source']}")