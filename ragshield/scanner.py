from __future__ import annotations

from pathlib import Path

from .detector import detect_prompt_injection
from .models import Document
from .retrieval import SimpleRetriever, chunk_document


def load_markdown_corpus(corpus_dir: Path) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(corpus_dir.glob("*.md")):
        documents.append(
            Document(
                doc_id=path.stem,
                title=path.stem.replace("_", " ").title(),
                content=path.read_text(encoding="utf-8"),
                source=str(path),
                trust="untrusted" if "poison" in path.name or "ticket" in path.name else "internal",
            )
        )
    return documents


def scan_knowledge_base(documents: list[Document], queries: list[str], top_k: int = 4) -> dict:
    high_risk_chunks: list[dict] = []
    total_chunks = 0
    for document in documents:
        for chunk_id, text in chunk_document(document):
            total_chunks += 1
            detection = detect_prompt_injection(text) if text else None
            if detection and detection.score >= 25:
                high_risk_chunks.append(
                    {
                        "doc_id": document.doc_id,
                        "title": document.title,
                        "chunk_id": chunk_id,
                        "score": detection.score,
                        "level": detection.level,
                        "categories": detection.categories,
                        "evidence": detection.evidence,
                        "action": detection.recommended_action,
                        "snippet": text[:360],
                    }
                )

    retriever = SimpleRetriever(documents)
    retrieval_findings: list[dict] = []
    poison_hits = 0
    total_retrievals = 0
    affected_queries = 0
    for query in queries:
        chunks = retriever.search(query, top_k=top_k)
        query_has_poison = False
        for rank, chunk in enumerate(chunks, start=1):
            total_retrievals += 1
            if chunk.detection.score >= 25:
                poison_hits += 1
                query_has_poison = True
                retrieval_findings.append(
                    {
                        "query": query,
                        "rank": rank,
                        "doc_id": chunk.doc_id,
                        "title": chunk.title,
                        "retrieval_score": round(chunk.score, 4),
                        "risk_score": chunk.detection.score,
                        "risk_level": chunk.detection.level,
                        "categories": chunk.detection.categories,
                        "snippet": chunk.text[:300],
                    }
                )
        if query_has_poison:
            affected_queries += 1

    poison_retrieval_rate = poison_hits / total_retrievals if total_retrievals else 0.0
    affected_query_rate = affected_queries / len(queries) if queries else 0.0
    return {
        "document_count": len(documents),
        "chunk_count": total_chunks,
        "high_risk_chunk_count": len(high_risk_chunks),
        "high_risk_chunks": high_risk_chunks,
        "queries": queries,
        "top_k": top_k,
        "poison_retrieval_rate": round(poison_retrieval_rate, 4),
        "affected_query_rate": round(affected_query_rate, 4),
        "retrieval_findings": retrieval_findings,
    }
