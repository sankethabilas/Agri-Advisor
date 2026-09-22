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

    print("\nSearch Results:")

    for i in range(3):
        print(f"\nRank {i + 1}")
        print(f"ID: {results['ids'][0][i]}")
        print(f"Distance: {results['distances'][0][i]}")
        print(f"Title: {results['metadatas'][0][i]['title']}")
        print(f"Crop: {results['metadatas'][0][i]['crop']}")
        print(f"Category: {results['metadatas'][0][i]['category']}")