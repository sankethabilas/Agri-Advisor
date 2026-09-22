import chromadb
from chromadb.utils import embedding_functions


# Connect to the existing persistent ChromaDB
chroma_client = chromadb.PersistentClient(
    path="./chroma_store"
)


# Use the same embedding model
embedding_function = (
    embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
)


# Get the existing collection
collection = chroma_client.get_collection(
    name="agri_knowledge_base",
    embedding_function=embedding_function
)


# Required smoke-test query
query = "rice yellow spots"


# Retrieve top 3 results
results = collection.query(
    query_texts=[query],
    n_results=3
)


print(f"\nTop 3 results for: '{query}'\n")

for i in range(3):

    print("=" * 70)
    print(f"Rank: {i + 1}")
    print(f"ID: {results['ids'][0][i]}")
    print(f"Distance: {results['distances'][0][i]}")
    print(f"Title: {results['metadatas'][0][i]['title']}")
    print(f"Crop: {results['metadatas'][0][i]['crop']}")
    print(f"Category: {results['metadatas'][0][i]['category']}")
    print(f"Source: {results['metadatas'][0][i]['source']}")
    print(f"\nText:\n{results['documents'][0][i]}")