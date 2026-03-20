from vectorstore.chroma_client import get_chroma_client
from retrieval.unified_retriever import unified_retrieve
from retrieval.exact_answer_extractor import extract_exact_answer
from llm.answer_generator import generate_answer

db = get_chroma_client()


def answer_query(user_query: str) -> str:
    retrieved_text, sources = unified_retrieve(user_query, db)

    if not retrieved_text:
        return "I could not find relevant information for this query in the project knowledge base."

    jira_sources  = [s for s in sources if s.startswith("JIRA-")]
    doc_sources   = [s for s in sources if s.startswith("DOC-")]
    other_sources = [s for s in sources if not s.startswith("JIRA-") and not s.startswith("DOC-")]

    print(f"[Main] JIRA sources : {jira_sources}")
    print(f"[Main] Doc  sources : {doc_sources}")
    print(f"[Main] Other sources: {other_sources}")

    from retrieval.intent_parser import parse_intent
    intent = parse_intent(user_query)

    # Lookup ticket intent — return pre-formatted response directly
    if intent["lookup_ticket"] and len(sources) == 1:
        return f"{retrieved_text}\n\n[Source: {sources[0]}]"

    # Single JIRA ticket — exact field answer mode
    if len(sources) == 1 and sources[0].startswith("JIRA-"):
        meta_result = db.get(where={"source": sources[0]})
        if meta_result["metadatas"]:
            meta = meta_result["metadatas"][0]
            exact = extract_exact_answer(user_query, retrieved_text, meta)
            return f"{exact}\n\n[Source: {sources[0]}]"

    # ✅ Multi-source — label each source in context so Groq knows what came from where
    labelled_context = f"[Source: {', '.join(sources)}]\n\n{retrieved_text}"
    summary = generate_answer(user_query, labelled_context)
    src_list = "\n".join(f"- {s}" for s in sources)

    return f"{summary}\n\n[Sources:]\n{src_list}"


if __name__ == "__main__":
    print("\n=== RAG Query Interface ===")
    print("Type your question and press Enter. Press Ctrl+C to exit.\n")

    while True:
        try:
            query = input("Query: ").strip()
            if not query:
                continue
            answer = answer_query(query)
            print(f"\n{answer}\n")
            print("-" * 60)
        except KeyboardInterrupt:
            print("\n\n[Exiting] Goodbye!")
            break