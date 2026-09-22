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

# ensure initializes correctly and connects to the existing ChromaDB collection
if __name__ == "__main__":
    agent = RAGAgent()
    print("RAG Agent initialized successfully.")
    print(f"Collection: {agent.collection.name}")
    print(f"Documents: {agent.collection.count()}")