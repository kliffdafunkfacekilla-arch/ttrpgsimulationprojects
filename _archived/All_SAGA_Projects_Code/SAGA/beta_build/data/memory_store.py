import os
import chromadb
from chromadb.config import Settings

class MemoryStore:
    """
    Manages long-term narrative memory using ChromaDB.
    Enables RAG (Retrieval-Augmented Generation) for the Game Master.
    """
    def __init__(self, db_path: str = "./runtime_data/vector_db"):
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Collection for campaign narrative events
        self.collection = self.client.get_or_create_collection(
            name="campaign_memory",
            metadata={"hnsw:space": "cosine"}
        )

    def store_event(self, event_id: str, text: str, metadata: dict = None):
        """
        Stores a piece of narrative history.
        """
        meta = metadata or {}
        self.collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[event_id]
        )

    def query_history(self, query: str, n_results: int = 3) -> list:
        """
        Retrieves the most relevant past events based on the current context query.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results or not results['documents']:
            return []
            
        return results['documents'][0]
