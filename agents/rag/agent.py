"""RAG / Information Retrieval Specialist Agent for Agri-Advisor (Subtasks T-02.4, T-22.2 & T-23). Performs semantic search over the verified agricultural knowledge corpus stored in ChromaDB and uses keyword fallback when semantic retrieval confidence is too low."""

import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.utils import embedding_functions

from agents.rag.keyword_search import KeywordSearcher
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

    def __init__(
        self,
        chroma_path: Optional[str] = None,
        fallback_threshold: float = 0.60,
    ):
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
        self.keyword_searcher = KeywordSearcher()
        self.fallback_threshold = fallback_threshold
        self.last_retrieval_method = "semantic"
        self.last_top_similarity = 0.0

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

    @staticmethod
    def distance_to_similarity(distance: float) -> float:
        """Convert Chroma L2 distance on normalized embeddings into similarity."""
        return max(0.0, min(1.0, 1.0 - (float(distance) / 2.0)))

    def get_top_similarity(self, results: Dict[str, Any]) -> float:
        """Return similarity of the top semantic result."""
        if not results:
            return 0.0

        distances = results.get("distances")
        if not distances or not distances[0]:
            return 0.0

        return self.distance_to_similarity(distances[0][0])

    @staticmethod
    def cosine_similarity(vector_a, vector_b) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        norm_a = math.sqrt(sum(value * value for value in vector_a))
        norm_b = math.sqrt(sum(value * value for value in vector_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        similarity = dot_product / (norm_a * norm_b)
        return max(0.0, min(1.0, similarity))

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

    def build_keyword_sources(
        self,
        keyword_results: List[Dict[str, Any]],
        query_embedding,
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        """Convert keyword-search results into the existing RagSourceItem-compatible structure."""
        if not keyword_results:
            return [], []

        max_keyword_score = max(float(item.get("keyword_score", 0.0)) for item in keyword_results)
        query_vector = query_embedding[0]
        ranked_sources = []

        for item in keyword_results:
            text = str(item.get("text", ""))
            document_embedding = self.embedding_function([text])[0]
            semantic_similarity = self.cosine_similarity(query_vector, document_embedding)
            raw_keyword_score = float(item.get("keyword_score", 0.0))
            keyword_relevance = raw_keyword_score / max_keyword_score if max_keyword_score > 0 else 0.0
            fallback_confidence = 0.70 * keyword_relevance + 0.30 * semantic_similarity

            source_id = item.get("source_id") or item.get("id")
            source_name = item.get("source") or "Department of Agriculture Sri Lanka"

            source = {
                "id": str(item.get("id") or source_id),
                "document_id": str(source_id),
                "title": str(item.get("title") or "Agricultural Advisory Document"),
                "section": str(item.get("category") or "General Agricultural Guidelines"),
                "content": text,
                "crop": item.get("crop"),
                "category": item.get("category"),
                "language": item.get("language") or "en",
                "source": source_name,
                "source_id": source_id,
                "author_organization": source_name,
                "region": item.get("region") or "Sri Lanka",
                "season": item.get("season") or "General",
                "score": round(fallback_confidence, 4),
            }
            ranked_sources.append((fallback_confidence, source))

        ranked_sources.sort(key=lambda item: item[0], reverse=True)
        sources = [item[1] for item in ranked_sources]
        confidence = [round(item[0], 4) for item in ranked_sources]
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

    def keyword_fallback(
        self,
        query: str,
        query_embedding,
        top_k: int,
        crop_filter: Optional[str],
        category_filter: Optional[str],
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        """Run metadata-aware keyword fallback search."""
        keyword_results = self.keyword_searcher.search(
            query=query,
            top_k=top_k,
            crop_filter=crop_filter,
            category_filter=category_filter,
        )

        if not keyword_results:
            return [], []

        return self.build_keyword_sources(keyword_results, query_embedding)

    def retrieve(self, request: RagRetrieveRequest) -> RagRetrieveResponse:
        """Execute end-to-end RAG retrieval matching the API contract."""
        start_time = time.perf_counter()
        self.last_retrieval_method = "semantic"
        self.last_top_similarity = 0.0

        query_embedding = self.encode_query(request.query)

        results = self.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            crop_filter=request.crop_filter,
            category_filter=request.category_filter,
        )

        top_similarity = self.get_top_similarity(results)
        self.last_top_similarity = top_similarity

        sources_raw, confidence = self.build_sources(
            results,
            min_score=request.min_score,
        )

        effective_fallback_threshold = max(self.fallback_threshold, request.min_score)
        fallback_required = not sources_raw or top_similarity < effective_fallback_threshold

        if fallback_required:
            keyword_sources, keyword_confidence = self.keyword_fallback(
                query=request.query,
                query_embedding=query_embedding,
                top_k=request.top_k,
                crop_filter=request.crop_filter,
                category_filter=request.category_filter,
            )

            if keyword_sources:
                sources_raw = keyword_sources
                confidence = keyword_confidence
                self.last_retrieval_method = "keyword_fallback"

        # If strict crop filter gave 0 results, fall back to unfiltered search to ensure grounded context
        if not sources_raw and request.crop_filter:
            results = self.search(
                query_embedding=query_embedding,
                top_k=request.top_k,
                crop_filter=None,
                category_filter=request.category_filter,
            )
            self.last_top_similarity = self.get_top_similarity(results)
            sources_raw, confidence = self.build_sources(
                results,
                min_score=request.min_score,
            )

            if sources_raw:
                self.last_retrieval_method = "semantic_unfiltered"

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
                vector_distance_metric="l2",
                execution_time_ms=elapsed_ms,
            ),
        )


rag_agent = RAGAgent()