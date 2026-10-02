"""
RAG / Information Retrieval Specialist Agent for Agri-Advisor (Subtask T-02.4 & T-22.2).
Performs semantic search over the verified Department of Agriculture knowledge corpus stored in ChromaDB.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import chromadb
from chromadb.utils import embedding_functions

from orchestrator.schemas import (
    RagMetadata,
    RagRetrieveRequest,
    RagRetrieveResponse,
    RagSourceItem,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_STORE_PATH = PROJECT_ROOT / "chroma_store"


class RAGAgent:
    """RAG Agent for semantic vector retrieval over DOA/IRRI agricultural corpus."""

    def __init__(self, chroma_path: Optional[str] = None):
        self.chroma_path = chroma_path or str(CHROMA_STORE_PATH)
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        self.embedding_function = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="agri_knowledge_base",
            embedding_function=self.embedding_function,
        )

    def encode_query(self, query: str):
        """Convert the farmer query into an embedding vector."""
        return self.embedding_function([query])

    @staticmethod
    def normalize_crop_filter(crop: Optional[str]) -> Optional[List[str]]:
        if not crop:
            return None
        c = crop.strip().lower()
        alias_map = {
            "paddy": ["rice", "Rice", "paddy", "Paddy"],
            "rice": ["rice", "Rice", "paddy", "Paddy"],
            "chilli": ["chilli", "Chilli", "chili", "Chili"],
            "chili": ["chilli", "Chilli", "chili", "Chili"],
            "tomato": ["tomato", "Tomato"],
            "maize": ["maize", "Maize", "corn", "Corn"],
            "corn": ["maize", "Maize", "corn", "Corn"],
            "mungbean": ["mungbean", "Mungbean", "mung bean", "Mung Bean"],
            "cowpea": ["cowpea", "Cowpea"],
            "finger millet": ["finger millet", "Finger Millet", "finger_millet"],
        }
        return alias_map.get(c, [c, c.capitalize(), c.title(), c.upper()])

    def search(
        self,
        query_embedding,
        top_k: int = 3,
        crop_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
    ):
        """Search ChromaDB for most similar documents with optional filters."""
        filters = []
        if crop_filter:
            variants = self.normalize_crop_filter(crop_filter)
            if variants and len(variants) == 1:
                filters.append({"crop": {"$eq": variants[0]}})
            elif variants:
                filters.append({"crop": {"$in": variants}})

        if category_filter:
            filters.append({"category": {"$in": [category_filter.lower(), category_filter.capitalize(), category_filter.title()]}})

        query_args: Dict[str, Any] = {
            "query_embeddings": query_embedding,
            "n_results": top_k,
        }
        if len(filters) == 1:
            query_args["where"] = filters[0]
        elif len(filters) > 1:
            query_args["where"] = {"$and": filters}

        return self.collection.query(**query_args)

    def build_sources(self, results: Dict[str, Any], min_score: float = 0.50) -> Tuple[List[Dict[str, Any]], List[float]]:
        """Build source information and similarity scores from ChromaDB results."""
        sources: List[Dict[str, Any]] = []
        confidence: List[float] = []

        if not results or not results.get("ids") or not results["ids"][0]:
            return sources, confidence

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        for i in range(len(ids)):
            # Distance metric: in ChromaDB L2 space on normalized embeddings,
            # cos_sim = 1 - (dist / 2.0). Map to [0.0, 1.0].
            if distances and i < len(distances):
                dist = float(distances[i])
                similarity = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
            else:
                similarity = 0.85

            # Allow relevant results with standard similarity threshold
            if similarity < min_score:
                continue

            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            doc_text = documents[i] if documents and i < len(documents) else ""

            source = {
                "id": str(ids[i]),
                "document_id": str(meta.get("source_id") or ids[i]),
                "title": str(meta.get("title") or "DOA Agricultural Advisory Document"),
                "section": str(meta.get("category") or "General Agricultural Guidelines"),
                "content": doc_text,
                "crop": meta.get("crop"),
                "category": meta.get("category"),
                "language": meta.get("language") or "en",
                "source": meta.get("source") or "Department of Agriculture Sri Lanka",
                "source_id": meta.get("source_id") or str(ids[i]),
                "author_organization": meta.get("source") or "Department of Agriculture Sri Lanka",
                "region": meta.get("region") or "Sri Lanka",
                "season": meta.get("season") or "General",
                "score": round(similarity, 4),
            }
            sources.append(source)
            confidence.append(round(similarity, 4))

        return sources, confidence

    def build_context(self, sources: List[Dict[str, Any]]) -> str:
        """Combine retrieved document passages into a formatted context string."""
        if not sources:
            return ""
        passages = []
        for s in sources:
            title = s.get("title", "")
            content = s.get("content", "")
            passages.append(f"[{title}]\n{content}")
        return "\n\n".join(passages)

    def retrieve(self, request: RagRetrieveRequest) -> RagRetrieveResponse:
        """Execute end-to-end RAG retrieval matching the API contract."""
        start_time = time.perf_counter()

        query_embedding = self.encode_query(request.query)

        results = self.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            crop_filter=request.crop_filter,
            category_filter=request.category_filter,
        )

        sources_raw, confidence = self.build_sources(
            results,
            min_score=request.min_score,
        )

        # If strict crop filter gave 0 results, fall back to unfiltered search to ensure grounded context
        if not sources_raw and request.crop_filter:
            results = self.search(
                query_embedding=query_embedding,
                top_k=request.top_k,
                crop_filter=None,
                category_filter=request.category_filter,
            )
            sources_raw, confidence = self.build_sources(
                results,
                min_score=request.min_score,
            )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        typed_sources: List[RagSourceItem] = [
            RagSourceItem.model_validate(src) for src in sources_raw
        ]

        context = self.build_context(sources_raw)

        return RagRetrieveResponse(
            context=context,
            sources=typed_sources,
            confidence=confidence,
            metadata=RagMetadata(
                total_chunks_retrieved=len(typed_sources),
                query_embedding_model="all-MiniLM-L6-v2",
                vector_distance_metric="cosine",
                execution_time_ms=elapsed_ms,
            ),
        )


rag_agent = RAGAgent()