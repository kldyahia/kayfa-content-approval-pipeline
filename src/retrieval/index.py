import chromadb
from pathlib import Path
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from .ingest import get_kb_nodes

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
COLLECTION_NAME = "kayfa_kb"

def get_vector_store(chroma_dir: str | Path = "storage/chroma_db") -> ChromaVectorStore:
    chroma_dir = Path(chroma_dir)
    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(COLLECTION_NAME)
    return ChromaVectorStore(chroma_collection=collection)

def build_index(
    kb_dir: str | Path = "data/knowledge_base",
    chroma_dir: str | Path = "storage/chroma_db"
) -> VectorStoreIndex:
    nodes = get_kb_nodes(kb_dir)
    if not nodes:
        raise RuntimeError(f"No documents/nodes generated from {kb_dir}")

    vector_store = get_vector_store(chroma_dir)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex(nodes, storage_context=storage_context, show_progress=False)

def load_index(chroma_dir: str | Path = "storage/chroma_db") -> VectorStoreIndex:
    vector_store = get_vector_store(chroma_dir)
    return VectorStoreIndex.from_vector_store(vector_store=vector_store)