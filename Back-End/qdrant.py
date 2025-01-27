import logging
import sys
import os
import yaml
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

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

model_name = config.get("model", "llama3.2")
system_prompt = config.get("system_prompt", "")
settings = config.get("settings", {})

llm = Ollama(
    model=model_name,
    system_prompt=system_prompt,
    max_tokens=settings.get("max_tokens", 500),
    temperature=settings.get("temperature", 0.7),
    top_p=settings.get("top_p", 0.9),
    presence_penalty=settings.get("presence_penalty", 0),
    frequency_penalty=settings.get("frequency_penalty", 0),
)

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