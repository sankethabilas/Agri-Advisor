# import necessary libraries (json and chromadb)
import json
import chromadb
# import the embedding functions from chromadb
from chromadb.utils import embedding_functions

# 1. Initialize persistent ChromaDB

# ChromaDB creates/opens a local databse inside ./chroma_store
chroma_client = chromadb.PersistentClient(
    path="./chroma_store"
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


# 5. Index documents into ChromaDB 

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
    metadatas = []

    #go thrhugh each document in the documents list and extract the id, text, and metadata
    for document in documents:

        # Store the unique document ID
        ids.append(document["id"])

        # Store the actual text of the document
        texts.append(document["text"])

        # Store the metadata for the document
        metadata = {
            "title": document["title"],
            "crop": document["crop"],
            "category": document["category"],
            "source": document["source"],
            "region": document["region"],
            "season": document["season"]
        }

        metadatas.append(metadata)

    #insert/update documents in ChromaDB

    # upsert() means:
    #     INSERT if the ID does not already exist
    #     UPDATE if the ID already exists

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas
    )

    #display the results
    print()
    print("Indexing complete.")
    print(f"Source document count : {len(documents)}")
    print(f"ChromaDB document count: {collection.count()}")


# 6. Main

if __name__ == "__main__":

    index_documents(
        "knowledge_base/documents.json"
    )