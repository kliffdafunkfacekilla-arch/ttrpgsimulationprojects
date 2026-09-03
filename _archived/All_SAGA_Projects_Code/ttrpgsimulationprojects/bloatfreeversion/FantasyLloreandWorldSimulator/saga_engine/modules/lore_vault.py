import chromadb
import os
import glob
from saga_engine.core.bus import EventBus

class LoreVaultDB:
    """The persistent memory of the Shatterlands. Indexes the Obsidian vault into ChromaDB."""
    
    def __init__(self, bus: EventBus, vault_path: str = "Shatterlands"):
        self.bus = bus
        self.vault_path = vault_path
        self.client = chromadb.PersistentClient(path="./lore_vault_db")
        self.collection = self.client.get_or_create_collection(name="shatterlands_lore")
        
        # Subscribe to query events
        self.bus.subscribe("LORE_QUERY", self.handle_query)

    def index_vault(self):
        """Crawls the Obsidian vault and embeds all markdown files."""
        print(f"[LORE VAULT] Indexing vault at {self.vault_path}...")
        md_files = glob.glob(os.path.join(self.vault_path, "**/*.md"), recursive=True)
        
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    file_name = os.path.basename(file_path)
                    
                    # Simple indexing: ID is filename, document is content
                    self.collection.add(
                        documents=[content],
                        metadatas=[{"source": file_path}],
                        ids=[file_name]
                    )
            except Exception as e:
                print(f"[LORE VAULT ERROR] Failed to index {file_path}: {e}")
        
        print(f"[LORE VAULT] Indexing complete. Total documents: {self.collection.count()}")

    def handle_query(self, payload: dict):
        """Responds to LORE_QUERY events from the Director."""
        query_text = payload.get("text", "")
        results = self.collection.query(
            query_texts=[query_text],
            n_results=3
        )
        
        # Combine results into context
        context = "\n---\n".join(results['documents'][0])
        self.bus.publish("LORE_RESULT", {"context": context, "query": query_text})

    def start_daemon(self):
        """Standard entry point for the background thread."""
        self.index_vault()
        print("[LORE VAULT] Daemon active and listening for queries.")
