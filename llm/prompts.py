QUERY_REWRITE_PROMPT = """
Rewrite the following user query into a detailed, explicit, context-rich search query
that will match technical documents, requirements, and project descriptions.

Original query:
{query}

Rewritten query:
"""


ANSWER_PROMPT = """You are a strict project knowledge assistant. Answer the question using ONLY \
the information in the context below. Do not use any outside knowledge or make assumptions.

Rules:
1. Only use facts explicitly stated in the context
2. If the context contains a partial answer, provide what is available and note what is missing
3. If the context is completely unrelated to the question, respond with: "I could not find relevant information for this query in the project knowledge base."
4. Do not generate examples or explanations not present in the context
5. Be concise, structured, and factual
6. Use bullet points when listing multiple items

Question: {question}

Context:
{context}

Answer:"""