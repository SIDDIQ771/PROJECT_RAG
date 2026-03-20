from vectorstore.chroma_client import get_chroma_client

db = get_chroma_client()
results = db.query(query_texts=["test"], n_results=5)
print(results)
