from agents.rag.agent import RAGAgent


# ============================================================
# Helpers
# ============================================================

def create_agent_without_init():
    """
    Create a RAGAgent instance without running __init__.

    This avoids connecting to ChromaDB or loading the
    embedding model inside each individual unit test.
    """
    return RAGAgent.__new__(RAGAgent)


def make_results(
    ids,
    distances,
    titles=None,
    documents=None,
):
    """
    Create a fake ChromaDB query result.
    """

    titles = titles or [
        f"Document {i + 1}"
        for i in range(len(ids))
    ]

    documents = documents or [
        f"Content {i + 1}"
        for i in range(len(ids))
    ]

    metadatas = []

    for i, document_id in enumerate(ids):
        metadatas.append(
            {
                "title": titles[i],
                "crop": "rice",
                "category": "disease",
                "language": "en",
                "source": "Test Agricultural Source",
                "source_id": document_id,
                "region": "Sri Lanka",
                "season": "general",
            }
        )

    return {
        "ids": [ids],
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
    }


class FakeCollection:
    """
    Small fake Chroma collection used to verify
    how search() builds query arguments.
    """

    def __init__(self):
        self.last_query = None

    def query(self, **kwargs):
        self.last_query = kwargs

        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }


class FakeKeywordSearcher:

    def __init__(self, results):
        self.results = results
        self.last_query = None

    def search(
        self,
        query,
        top_k,
        crop_filter=None,
        category_filter=None,
    ):
        self.last_query = {
            "query": query,
            "top_k": top_k,
            "crop_filter": crop_filter,
            "category_filter": category_filter,
        }

        return self.results


# ============================================================
# T-27.2.1
# Distance to similarity conversion
# ============================================================

def test_distance_to_similarity():

    assert (
        RAGAgent.distance_to_similarity(0.0)
        == 1.0
    )

    assert (
        RAGAgent.distance_to_similarity(1.0)
        == 0.5
    )

    assert (
        RAGAgent.distance_to_similarity(2.0)
        == 0.0
    )


# ============================================================
# T-27.2.2
# Rice / paddy aliases
# ============================================================

def test_normalize_rice_crop_alias():

    result = (
        RAGAgent.normalize_crop_filter(
            "paddy"
        )
    )

    assert "rice" in result
    assert "Rice" in result
    assert "paddy" in result
    assert "Paddy" in result


# ============================================================
# T-27.2.3
# Chilli / chili aliases
# ============================================================

def test_normalize_chilli_crop_alias():

    result = (
        RAGAgent.normalize_crop_filter(
            "chili"
        )
    )

    assert "chilli" in result
    assert "Chilli" in result
    assert "chili" in result
    assert "Chili" in result


# ============================================================
# T-27.2.4
# No crop filter
# ============================================================

def test_normalize_crop_filter_none():

    result = (
        RAGAgent.normalize_crop_filter(
            None
        )
    )

    assert result is None


# ============================================================
# T-27.2.5
# Basic semantic retrieval call
# ============================================================

def test_search_uses_top_k():

    agent = create_agent_without_init()

    fake_collection = FakeCollection()

    agent.collection = fake_collection

    fake_embedding = [
        [0.1, 0.2, 0.3]
    ]

    agent.search(
        query_embedding=fake_embedding,
        top_k=3,
    )

    assert (
        fake_collection.last_query[
            "query_embeddings"
        ]
        == fake_embedding
    )

    assert (
        fake_collection.last_query[
            "n_results"
        ]
        == 3
    )

    assert (
        "where"
        not in fake_collection.last_query
    )


# ============================================================
# T-27.2.6
# Crop and category filters
# ============================================================

def test_search_builds_crop_and_category_filters():

    agent = create_agent_without_init()

    fake_collection = FakeCollection()

    agent.collection = fake_collection

    agent.search(
        query_embedding=[
            [0.1, 0.2]
        ],
        top_k=3,
        crop_filter="rice",
        category_filter="disease",
    )

    where = (
        fake_collection.last_query[
            "where"
        ]
    )

    assert "$and" in where

    assert len(
        where["$and"]
    ) == 2


# ============================================================
# T-27.2.7
# Ranking order
# ============================================================

def test_build_sources_preserves_ranking_order():

    agent = create_agent_without_init()

    results = make_results(
        ids=[
            "DOC-001",
            "DOC-002",
            "DOC-003",
        ],
        distances=[
            0.10,
            0.30,
            0.60,
        ],
    )

    sources, confidence = (
        agent.build_sources(
            results,
            min_score=0.50,
        )
    )

    assert len(sources) == 3

    assert (
        sources[0]["id"]
        == "DOC-001"
    )

    assert (
        sources[1]["id"]
        == "DOC-002"
    )

    assert (
        sources[2]["id"]
        == "DOC-003"
    )

    assert (
        confidence[0]
        >= confidence[1]
        >= confidence[2]
    )


# ============================================================
# T-27.2.8
# Source metadata return
# ============================================================

def test_build_sources_returns_source_metadata():

    agent = create_agent_without_init()

    results = make_results(
        ids=[
            "R-D-008"
        ],
        distances=[
            0.20
        ],
        titles=[
            "Bacterial Leaf Blight"
        ],
        documents=[
            "Bacterial leaf blight affects rice."
        ],
    )

    sources, confidence = (
        agent.build_sources(
            results,
            min_score=0.50,
        )
    )

    assert len(sources) == 1
    assert len(confidence) == 1

    source = sources[0]

    assert (
        source["id"]
        == "R-D-008"
    )

    assert (
        source["title"]
        == "Bacterial Leaf Blight"
    )

    assert (
        source["crop"]
        == "rice"
    )

    assert (
        source["category"]
        == "disease"
    )

    assert (
        source["source"]
        == "Test Agricultural Source"
    )

    assert (
        source["region"]
        == "Sri Lanka"
    )


# ============================================================
# T-27.2.9
# Empty result handling
# ============================================================

def test_build_sources_handles_empty_result():

    agent = create_agent_without_init()

    results = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    sources, confidence = (
        agent.build_sources(
            results
        )
    )

    assert sources == []
    assert confidence == []


# ============================================================
# T-27.2.10
# Low similarity result filtering
# ============================================================

def test_build_sources_rejects_low_similarity():

    agent = create_agent_without_init()

    results = make_results(
        ids=[
            "LOW-001"
        ],
        distances=[
            1.50
        ],
    )

    # similarity:
    #
    # 1 - (1.50 / 2)
    # = 0.25
    #
    # min_score = 0.50
    # therefore document should be rejected.

    sources, confidence = (
        agent.build_sources(
            results,
            min_score=0.50,
        )
    )

    assert sources == []
    assert confidence == []


# ============================================================
# T-27.2.11
# Top semantic similarity
# ============================================================

def test_get_top_similarity():

    agent = create_agent_without_init()

    results = make_results(
        ids=[
            "DOC-001"
        ],
        distances=[
            0.20
        ],
    )

    similarity = (
        agent.get_top_similarity(
            results
        )
    )

    assert similarity == 0.9


# ============================================================
# T-27.2.12
# Empty top similarity
# ============================================================

def test_get_top_similarity_empty():

    agent = create_agent_without_init()

    results = {
        "ids": [[]],
        "distances": [[]],
    }

    similarity = (
        agent.get_top_similarity(
            results
        )
    )

    assert similarity == 0.0


# ============================================================
# T-27.2.13
# Context generation
# ============================================================

def test_build_context():

    agent = create_agent_without_init()

    sources = [
        {
            "title": "Brown Spot",
            "content":
                "Brown spot affects rice leaves.",
        },
        {
            "title": "Leaf Scald",
            "content":
                "Leaf scald affects rice.",
        },
    ]

    context = (
        agent.build_context(
            sources
        )
    )

    assert (
        "[Brown Spot]"
        in context
    )

    assert (
        "Brown spot affects rice leaves."
        in context
    )

    assert (
        "[Leaf Scald]"
        in context
    )

    assert (
        "Leaf scald affects rice."
        in context
    )


# ============================================================
# T-27.2.14
# Empty context
# ============================================================

def test_build_context_empty():

    agent = create_agent_without_init()

    assert (
        agent.build_context([])
        == ""
    )


# ============================================================
# T-27.2.15
# Keyword fallback search
# ============================================================

def test_keyword_fallback_returns_keyword_sources():

    agent = create_agent_without_init()

    keyword_results = [
        {
            "id": "T-D-003",
            "title":
                "Tomato Late Blight",
            "text":
                "Late blight affects tomato plants.",
            "crop": "tomato",
            "category": "disease",
            "keyword_score": 10.0,
        }
    ]

    agent.keyword_searcher = (
        FakeKeywordSearcher(
            keyword_results
        )
    )

    expected_sources = [
        {
            "id": "T-D-003",
            "title":
                "Tomato Late Blight",
        }
    ]

    expected_confidence = [
        0.90
    ]

    agent.build_keyword_sources = (
        lambda results, embedding:
        (
            expected_sources,
            expected_confidence,
        )
    )

    sources, confidence = (
        agent.keyword_fallback(
            query=
                "tomato late blight",
            query_embedding=[
                [0.1, 0.2]
            ],
            top_k=3,
            crop_filter="tomato",
            category_filter="disease",
        )
    )

    assert (
        sources
        == expected_sources
    )

    assert (
        confidence
        == expected_confidence
    )


# ============================================================
# T-27.2.16
# Exact-title rescue
# ============================================================

def test_keyword_title_rescue_matches_explicit_title():

    agent = create_agent_without_init()

    keyword_results = [
        {
            "id": "T-D-003",
            "title":
                "Tomato Late Blight",
            "text":
                "Late blight affects tomato plants.",
            "crop": "tomato",
            "category": "disease",
            "keyword_score": 20.0,
        }
    ]

    agent.keyword_searcher = (
        FakeKeywordSearcher(
            keyword_results
        )
    )

    expected_sources = [
        {
            "id": "T-D-003",
            "title":
                "Tomato Late Blight",
        }
    ]

    expected_confidence = [
        0.92
    ]

    agent.build_keyword_sources = (
        lambda results, embedding:
        (
            expected_sources,
            expected_confidence,
        )
    )

    (
        sources,
        confidence,
        matched_phrase,
    ) = agent.keyword_title_rescue(
        query=
            "How do I manage tomato late blight?",
        query_embedding=[
            [0.1, 0.2]
        ],
        top_k=3,
        crop_filter="tomato",
        category_filter="disease",
    )

    assert (
        sources
        == expected_sources
    )

    assert (
        confidence
        == expected_confidence
    )

    assert (
        matched_phrase
        == "tomato late blight"
    )