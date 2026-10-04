# import necessary libraries (json and chromadb)
import json
from pathlib import Path

import chromadb
# import the embedding functions from chromadb
from chromadb.utils import embedding_functions

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHROMA_STORE_PATH = PROJECT_ROOT / "chroma_store"
DOCUMENTS_PATH = PROJECT_ROOT / "knowledge_base" / "documents.json"

# 1. Initialize persistent ChromaDB

# ChromaDB creates/opens a local databse inside ./chroma_store
chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_STORE_PATH)
)
# use persistent to store the data in a local directory called "chroma_store". 
# This allows the data to be saved and accessed later, even after the program has finished running.

# 2. Load the Sentence Transformer embedding model

embedding_function = (
    embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
)
# "Chilli has fungal diseases" is converted into a vector such as [0.12, -0.34, 0.76, ...]
# "all-MiniLM-L6-v2" is the Sentence Transformer model
# used to create these embeddings

# 3. Create or get the knowledge-base collection

collection = chroma_client.get_or_create_collection(
    name="agri_knowledge_base",
    embedding_function=embedding_function
)


# 4. Load documents.json

# "r" is used to read the file, and "utf-8" is used to handle any special characters in the text
# used bcz kb contain sinhala text too
def load_documents(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        documents = json.load(file)
         # Convert JSON data into Python objects
        # If documents.json contains a JSON array,
        # json.load() will give a Python list.

    return documents


# 5. Build T-23 retrieval text

# metadata-enriched text used only for embeddings
# the original document body is still stored separately in ChromaDB
# and returned to the RAG agent.
def build_embedding_text(document):
    title = str(document.get("title", "")).strip()
    crop = str(document.get("crop", "")).strip()
    category = str(document.get("category", "")).strip()
    region = str(document.get("region", "")).strip()
    season = str(document.get("season", "")).strip()
    text = str(document.get("text", "")).strip()

    return (
        f"Title: {title}\n"
        f"Crop: {crop}\n"
        f"Category: {category}\n"
        f"Region: {region}\n"
        f"Season: {season}\n"
        f"Content: {text}"
    )


# 6. Build metadata

def build_metadata(document):
    return {
        "title": document.get("title", ""),
        "crop": document.get("crop", ""),
        "category": document.get("category", ""),
        "language": document.get("language", "en"),
        "source": document.get("source", ""),
        "source_id": document.get("source_id", document.get("id", "")),
        "region": document.get("region", "Sri Lanka"),
        "season": document.get("season", "general"),
        "index_version": "t23_metadata_enriched_v1",
    }


# 7. Remove stale indexed records

def remove_stale_documents(current_document_ids):
    existing = collection.get()
    existing_ids = set(existing.get("ids", []))
    current_ids = set(current_document_ids)
    stale_ids = list(existing_ids - current_ids)

    if stale_ids:
        collection.delete(ids=stale_ids)
        print(f"Removed {len(stale_ids)} stale indexed documents.")
    else:
        print("No stale indexed documents found.")


# 8. Index documents into ChromaDB 

def index_documents(filepath):

    # Load the knowledge-base JSON file
    documents = load_documents(filepath)

    print(f"Loaded {len(documents)} documents from {filepath}")
     # len(documents) tells how many documents were loaded
    
    #create empty lists to store the document ids, texts, and metadata
    # ids       → unique document IDs
    # texts     → actual agriculture knowledge
    # metadatas → additional information about each document
    ids = []
    texts = []
    embedding_texts = []
    metadatas = []

    #go thrhugh each document in the documents list and extract the id, text, and metadata
    for document in documents:

        # Store the unique document ID
        ids.append(str(document["id"]))

        # Store the actual text of the document
        texts.append(str(document["text"]))

        # Store metadata-enriched text used only for retrieval embeddings
        embedding_texts.append(build_embedding_text(document))

        # Store the metadata for the document
        metadata = build_metadata(document)

        metadatas.append(metadata)

    # Remove stale IDs before re-indexing
    remove_stale_documents(ids)

    # Generate embeddings using the metadata-enriched retrieval text
    embeddings = embedding_function(embedding_texts)

    #insert/update documents in ChromaDB

    # upsert() means:
    #     INSERT if the ID does not already exist
    #     UPDATE if the ID already exists

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    #display the results
    print()
    print("Indexing complete.")
    print(f"Source document count : {len(documents)}")
    print(f"ChromaDB document count: {collection.count()}")

    if collection.count() != len(documents):
        raise ValueError("ChromaDB document count does not match documents.json.")


# 9. Main

if __name__ == "__main__":

    index_documents(
        DOCUMENTS_PATH
    )