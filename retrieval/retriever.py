from vectorstore.chroma_client import get_chroma_client


def retrieve_chunks(query: str, top_k: int = 9):
    """
    Retrieve top_k most relevant chunks from ALL sources (JIRA + Docs + Confluence).
    No source filtering — ChromaDB ranks by semantic similarity across everything.
    """
    db = get_chroma_client()
    results = db.query(query_texts=[query], n_results=top_k)

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i][:1500],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    # ✅ Debug: show what sources were retrieved
    sources = [c["metadata"].get("source", "unknown") for c in chunks]
    print(f"[Retriever] Retrieved {len(chunks)} chunks from sources: {sources}")

    return chunks