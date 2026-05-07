import re

STOPWORDS = {
    "what", "is", "the", "of", "a", "an",
    "does", "do", "how", "why",
    "tell", "me", "about"
}


def extract_entities(query: str):
    """
    Extract meaningful query entities.
    Example:
    'What is lexitasOne objective'
    -> ['lexitasone', 'objective']
    """

    tokens = re.findall(r"\b[A-Za-z0-9_-]+\b", query)

    entities = []

    for token in tokens:
        token = token.lower()

        if len(token) > 3 and token not in STOPWORDS:
            entities.append(token)

    return entities


def validate_query_entities(query: str, context: str):
    """
    Validate whether query entities exist
    in retrieved context.
    """

    entities = extract_entities(query)

    context_lower = context.lower()

    missing_entities = []

    for entity in entities:
        if entity not in context_lower:
            missing_entities.append(entity)

    return len(missing_entities) == 0, missing_entities