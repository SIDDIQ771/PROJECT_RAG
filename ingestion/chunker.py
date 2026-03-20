from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


def _clean_text(text: str) -> str:
    """Remove excessive whitespace and non-printable characters."""
    text = re.sub(r'\n{3,}', '\n\n', text)       # collapse 3+ newlines to 2
    text = re.sub(r'[ \t]{2,}', ' ', text)        # collapse multiple spaces
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)    # remove non-ASCII garbage
    return text.strip()


def _is_junk_chunk(text: str) -> bool:
    """
    Reject chunks that are mostly whitespace, page numbers, headers,
    or too short to carry meaning.
    """
    stripped = text.strip()
    if len(stripped) < 60:
        return True
    # Mostly digits/special chars (page numbers, table borders)
    alpha_ratio = sum(c.isalpha() for c in stripped) / max(len(stripped), 1)
    if alpha_ratio < 0.3:
        return True
    return False


def chunk_text(text: str) -> list[str]:
    """
    Optimized chunking strategy:
    - Clean text first
    - Use larger chunks (1200 chars) with significant overlap (300 chars)
      so a single mention mid-page is never split away from its context
    - Filter junk chunks
    - Return cleaned, meaningful chunks only
    """
    text = _clean_text(text)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,       # larger chunks = more context per chunk
        chunk_overlap=300,     # 25% overlap ensures boundary mentions are captured
        separators=[
            "\n\n",            # paragraph breaks first
            "\n",              # then line breaks
            ". ",              # then sentence boundaries
            ", ",
            " ",               # word boundaries last
            ""
        ],
        length_function=len,
        is_separator_regex=False,
    )

    chunks = splitter.split_text(text)

    # Filter junk and deduplicate
    seen = set()
    clean_chunks = []
    for chunk in chunks:
        chunk = chunk.strip()
        if _is_junk_chunk(chunk):
            continue
        # Deduplicate near-identical chunks (from overlap)
        signature = chunk[:80].lower().strip()
        if signature in seen:
            continue
        seen.add(signature)
        clean_chunks.append(chunk)

    return clean_chunks