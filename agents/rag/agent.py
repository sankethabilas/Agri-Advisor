#import the necessary libraries
import chromadb
from chromadb.utils import embedding_functions


class RAGAgent:
    def __init__(self):
        # Connect to the existing persistent ChromaDB store created in T-07.
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_store"
        )

        # Use the same embedding model that was used when indexing the knowledge
        # consume the already created knowledge base, not create a new one
        self.embedding_function = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

        # Connect to the existing knowledge-base collection
        self.collection = self.chroma_client.get_collection(
            name="agri_knowledge_base",
            embedding_function=self.embedding_function
        )

    # Encode a query into an embedding vector
    def encode_query(self, query: str):
        """
        Convert the farmer's query into an embedding vector
        using the same model used during knowledge-base indexing.
        """
        return self.embedding_function([query])

    # Search the knowledge base for the most relevant documents
    def search(self, query_embedding, top_k: int = 3):
        """
        Search ChromaDB for the most similar knowledge-base documents.
        """
        return self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )

    # combine the retrieved document texts into a single context string  
    def build_context(self, results):
        """
        Combine the retrieved document texts into a single context string.
        """
        documents = results["documents"][0]

        context = "\n\n".join(documents)

        return context

    def build_sources(self, results):
        """
        Build source information and similarity scores
        from the ChromaDB search results.
        """
        sources = []
        confidence = []

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for i in range(len(ids)):
            similarity = 1 - distances[i]

            metadata = metadatas[i]

            source = {
                "id": ids[i],
                "title": metadata["title"],
                "content": documents[i],
                "crop": metadata["crop"],
                "category": metadata["category"],
                "language": metadata["language"],
                "source": metadata["source"],
                "source_id": metadata["source_id"],
                "region": metadata["region"],
                "season": metadata["season"],
                "score": similarity
            }

            sources.append(source)
            confidence.append(similarity)

        return sources, confidence

# ensure initializes correctly and connects to the existing ChromaDB collection
if __name__ == "__main__":
    agent = RAGAgent()

    print("RAG Agent initialized successfully.")
    print(f"Collection: {agent.collection.name}")
    print(f"Documents: {agent.collection.count()}")

    query = "My rice leaves have yellow spots"

    embedding = agent.encode_query(query)

    print(f"Query: {query}")
    print(f"Embedding dimensions: {len(embedding[0])}")

    results = agent.search(
        query_embedding=embedding,
        top_k=3
    )

    print("\nRetrieved Metadata:")

    for metadata in results["metadatas"][0]:
        print(metadata)

    context = agent.build_context(results)

    print("\nRetrieved Context:")
    print(context)

    print("\nSearch Results:")

    for i in range(3):
        print(f"\nRank {i + 1}")
        print(f"ID: {results['ids'][0][i]}")
        print(f"Distance: {results['distances'][0][i]}")
        print(f"Title: {results['metadatas'][0][i]['title']}")
        print(f"Crop: {results['metadatas'][0][i]['crop']}")
        print(f"Category: {results['metadatas'][0][i]['category']}")
        print(f"Language: {results['metadatas'][0][i]['language']}")
        print(f"Source: {results['metadatas'][0][i]['source']}")
        print(f"Source ID: {results['metadatas'][0][i]['source_id']}")
        print(f"Region: {results['metadatas'][0][i]['region']}")
        print(f"Season: {results['metadatas'][0][i]['season']}")

    sources, confidence = agent.build_sources(results)

    print("\nSources:")

    for source in sources:
        print(source)

    print("\nConfidence:")
    print(confidence)