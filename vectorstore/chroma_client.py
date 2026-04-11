import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from config.settings import settings

embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-mpnet-base-v2",
    local_files_only=True  # ✅ Use cached model, no HuggingFace network call
)

def get_chroma_client():
    client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
    return client.get_or_create_collection(
        name="rag_collection",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )