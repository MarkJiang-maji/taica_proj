from __future__ import annotations

import math
import re
from collections import Counter

from .detector import detect_prompt_injection
from .models import Document, RetrievedChunk


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]{2,}")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def chunk_document(document: Document, max_words: int = 140) -> list[tuple[str, str]]:
    words = document.content.split()
    if not words:
        return [(f"{document.doc_id}:0", "")]
    chunks: list[tuple[str, str]] = []
    for idx in range(0, len(words), max_words):
        chunk_words = words[idx : idx + max_words]
        chunks.append((f"{document.doc_id}:{idx // max_words}", " ".join(chunk_words)))
    return chunks


class SimpleRetriever:
    def __init__(self, documents: list[Document], max_words: int = 140) -> None:
        self.documents = documents
        self.chunks: list[tuple[Document, str, str]] = []
        for document in documents:
            for chunk_id, chunk_text in chunk_document(document, max_words=max_words):
                self.chunks.append((document, chunk_id, chunk_text))
        self.doc_freq: Counter[str] = Counter()
        for _, _, text in self.chunks:
            self.doc_freq.update(set(tokenize(text)))
        self.total_chunks = max(1, len(self.chunks))

    def _vector(self, text: str) -> dict[str, float]:
        counts = Counter(tokenize(text))
        vector: dict[str, float] = {}
        for token, tf in counts.items():
            idf = math.log((1 + self.total_chunks) / (1 + self.doc_freq.get(token, 0))) + 1
            vector[token] = (1 + math.log(tf)) * idf
        return vector

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(weight * right.get(token, 0.0) for token, weight in left.items())
        left_norm = math.sqrt(sum(weight * weight for weight in left.values()))
        right_norm = math.sqrt(sum(weight * weight for weight in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    def search(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        query_vector = self._vector(query)
        scored: list[RetrievedChunk] = []
        for document, chunk_id, text in self.chunks:
            score = self._cosine(query_vector, self._vector(text))
            if score <= 0:
                continue
            scored.append(
                RetrievedChunk(
                    doc_id=document.doc_id,
                    title=document.title,
                    chunk_id=chunk_id,
                    text=text,
                    score=score,
                    detection=detect_prompt_injection(text),
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

