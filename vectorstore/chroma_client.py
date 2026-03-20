import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from config.settings import settings

# ✅ all-mpnet-base-v2 — significantly better than MiniLM for:
# - rare single mentions deep in large documents
# - semantic similarity across long contexts
# - distinguishing nuanced technical terms
# Tradeoff: ~420MB vs ~90MB for MiniLM, slightly slower to embed
embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

def get_chroma_client():
    client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
    return client.get_or_create_collection(
        name="rag_collection",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )