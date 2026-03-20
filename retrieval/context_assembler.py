def assemble_context(ranked_results, max_tokens=1800):
    context = ""
    token_count = 0

    for r in ranked_results:
        chunk = r["text"]
        tokens = len(chunk.split())

        if token_count + tokens > max_tokens:
            break

        context += f"\n\n[Source: {r['metadata']['source']}] {chunk}"
        token_count += tokens

    return context
