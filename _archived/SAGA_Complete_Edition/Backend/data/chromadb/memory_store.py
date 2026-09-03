import os
import uuid
import logging
import chromadb
from typing import Dict, Any
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryStore")

class MemoryStore:
    """
    Local Vector Database for the SAGA AI Director.
    Stores and retrieves narrative events using semantic search (RAG).
    """
    def __init__(self, persist_directory: str = "saves/vector_db"):
        # Ensure the save directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize the local persistent client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create the collection (cosine similarity works best for narrative matching)
        self.collection = self.client.get_or_create_collection(
            name="saga_campaign_memory",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"MemoryStore initialized successfully at: {persist_directory}")

    def store_event(self, text: str, metadata: Dict[str, Any] = None):
        """
        Saves a narrative chunk into the vector database.
        Example metadata: {"session_id": "001", "location": "The Rusty Boar Tavern"}
        """
        if not text or not text.strip():
            return

        event_id = str(uuid.uuid4())
        safe_metadata = metadata if metadata else {"type": "general_narrative"}

        try:
            self.collection.add(
                documents=[text.strip()],
                metadatas=[safe_metadata],
                ids=[event_id]
            )
            logger.debug(f"Memory stored: {text[:40]}...")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")

    def recall_context(self, query: str, n_results: int = 3) -> str:
        """
        Searches the database for past events semantically similar to the query.
        Returns a formatted string ready to be injected into the LLM prompt.
        """
        if not query or not query.strip():
            return ""

        try:
            # Query the local vector DB
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Extract documents
            documents = results.get('documents', [[]])[0]
            if not documents:
                return ""
            
            # Format the output for the AI Director
            recalled_text = "--- RELEVANT PAST EVENTS ---\n"
            for doc in documents:
                recalled_text += f"- {doc}\n"
            return recalled_text

        except Exception as e:
            logger.error(f"Failed to recall memory: {e}")
            return ""
