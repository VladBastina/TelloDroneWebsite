import logging
import sys
import os

import qdrant_client
from IPython.display import Markdown, display
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader,GPTVectorStoreIndex
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from qdrant_client.http.models import VectorParams , Distance

Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")

llm = Ollama(model = "llama3.2")

Settings.llm = llm
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

# Load documents
documents = SimpleDirectoryReader("./data/web_site/").load_data()

# Initialize Qdrant client (assuming Qdrant runs on localhost:6333)
client = qdrant_client.QdrantClient(
    host="localhost",
    port=6333
)

client.recreate_collection(
    collection_name="web_site",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

# Set up Qdrant vector store and storage context
vector_store = QdrantVectorStore(client=client, collection_name="web_site")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Create index from documents
index = GPTVectorStoreIndex.from_documents([],storage_context=storage_context)

for document in documents:
    index.update(document)

query_engine = index.as_query_engine()

def receive_answear(message:str)->str:
    response = query_engine.query(message)
    
    return response