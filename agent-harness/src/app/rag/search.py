"""Local search service for the knowledge base.

This is a simple TF-IDF-based search over indexed document chunks.
Students should extend or replace this with:
    - Sentence-transformer embeddings + cosine similarity
    - A vector database (ChromaDB, FAISS, etc.)
    - Hybrid search (keyword + semantic)
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from app.rag.indexer import KnowledgeBaseIndexer


class LocalSearchService:
    """Simple keyword search over indexed documents.

    Uses TF-IDF scoring for relevance ranking. Replace with
    embeddings-based search for production quality.
    """

    def __init__(self, indexer: KnowledgeBaseIndexer):
        self.indexer = indexer

    def search(self, query: str, top: int = 5) -> list[dict[str, Any]]:
        """Search the knowledge base for relevant document chunks.

        Args:
            query: Natural-language search query.
            top: Maximum number of results to return.

        Returns:
            List of result dicts with 'title', 'snippet', 'source', and 'score'.
        """
        documents = self.indexer.documents
        if not documents:
            return []

        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        # Build document frequency counts
        doc_freq: Counter = Counter()
        for doc in documents:
            doc_terms = set(self._tokenize(doc.get("content", "")))
            for term in doc_terms:
                doc_freq[term] += 1

        n_docs = len(documents)
        scored_results = []

        for doc in documents:
            content = doc.get("content", "")
            doc_terms = self._tokenize(content)
            if not doc_terms:
                continue

            term_freq = Counter(doc_terms)
            score = 0.0

            for term in query_terms:
                tf = term_freq.get(term, 0) / len(doc_terms)
                df = doc_freq.get(term, 0)
                idf = math.log((n_docs + 1) / (df + 1)) + 1
                score += tf * idf

            if score > 0:
                snippet = content[:300] + ("..." if len(content) > 300 else "")
                scored_results.append({
                    "title": doc.get("title", "Unknown"),
                    "snippet": snippet,
                    "source": doc.get("source", ""),
                    "score": round(score, 4),
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top]

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase terms."""
        return re.findall(r"\b[a-z0-9]+\b", text.lower())
