from groq import Groq
from config.settings import settings
from llm.prompts import ANSWER_PROMPT

client = Groq(api_key=settings.GROQ_API_KEY)

def generate_answer(query: str, context: str) -> str:
    if not context or not context.strip():
        return "I could not find relevant information for this query in the project knowledge base."

    # Truncate to stay within token limits
    context = context[:4000]

    prompt = ANSWER_PROMPT.format(question=query, context=context)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict project knowledge assistant. "
                    "Answer only from the context provided. "
                    "Never use outside knowledge or make up information. "
                    "If the answer is in the context, always provide it clearly."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1024,
        temperature=0.0,
    )

    answer = response.choices[0].message.content.strip()
    return answer if answer else "I could not find relevant information for this query in the project knowledge base."