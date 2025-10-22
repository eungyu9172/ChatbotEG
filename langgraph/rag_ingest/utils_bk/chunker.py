from typing import List
import tiktoken


def _tokenizer():
    # cl100k_base is compatible with GPT-4 family tokenization
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    enc = _tokenizer()
    return len(enc.encode(text))


def split_sentences(text: str) -> List[str]:
    # lightweight sentence split to avoid heavy deps
    parts = []
    buf = []
    for ch in text:
        buf.append(ch)
        if ch in ".?!\n":
            parts.append("".join(buf).strip())
            buf = []
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def chunk_text(text: str, chunk_size: int, overlap: int, min_chunk_tokens: int) -> List[str]:
    sents = split_sentences(text)
    enc = _tokenizer()
    chunks, cur, cur_tokens = [], [], 0
    for s in sents:
        t = enc.encode(s)
        if cur_tokens + len(t) <= chunk_size:
            cur.append(s)
            cur_tokens += len(t)
        else:
            if cur_tokens >= min_chunk_tokens:
                chunks.append(" ".join(cur).strip())
            # start new window with overlap
            if overlap > 0 and chunks:
                prev = enc.encode(chunks[-1])
                keep = max(0, len(prev) - overlap)
                # no expensive inverse; just drop overlap by resetting state
            cur, cur_tokens = [s], len(t)
    if cur and cur_tokens >= min_chunk_tokens:
        chunks.append(" ".join(cur).strip())
    # fallback: if empty due to min threshold, force one chunk by tokens
    if not chunks and text.strip():
        toks = enc.encode(text)
        for i in range(0, len(toks), chunk_size - overlap if chunk_size > overlap else chunk_size):
            seg = toks[i:i + chunk_size]
            chunks.append(enc.decode(seg))
    return chunks
