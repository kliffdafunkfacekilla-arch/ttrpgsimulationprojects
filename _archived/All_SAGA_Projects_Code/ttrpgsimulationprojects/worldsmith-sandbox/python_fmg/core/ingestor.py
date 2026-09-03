import os
import re
import sqlite3
import json
import glob

# Mock V12 Matrix for assigning base stats (6 Body, 6 Mind)
V12_MATRIX = {
    "Warden": {"might": 2, "agility": 3, "endurance": 4, "intellect": 1, "willpower": 2, "presence": 2},
    "Army": {"might": 5, "agility": 2, "endurance": 5, "intellect": 1, "willpower": 3, "presence": 3},
    "Paragon": {"might": 8, "agility": 8, "endurance": 8, "intellect": 8, "willpower": 8, "presence": 8},
    "Faction": {"might": 10, "agility": 5, "endurance": 10, "intellect": 10, "willpower": 10, "presence": 10}
}

class LoreIngestor:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def ingest_all(self, markdown_dir):
        print(f"Starting ingestion from {markdown_dir}")
        chapters = glob.glob(os.path.join(markdown_dir, "Chapter_*.md"))
        
        entities = []
        cells = []
        
        for chapter in chapters:
            with open(chapter, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 1. Regex Scrape
                # Simple extraction logic looking for patterns like [EntityName|EntityType] or [[CellName]]
                
                # Extract Cells [[CellName:Biome]]
                cell_matches = re.finditer(r'\[\[(.*?):(.*?)]]', content)
                for match in cell_matches:
                    name, biome = match.group(1).strip(), match.group(2).strip()
                    cells.append({"name": name, "biome": biome})
                    
                # Extract Entities [EntityName|EntityType]
                entity_matches = re.finditer(r'\[([^\[\]]+)\|([^\[\]]+)\]', content)
                for match in entity_matches:
                    name, e_type = match.group(1).strip(), match.group(2).strip()
                    entities.append({"name": name, "type": e_type})
        
        # Hydrate Database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Hydrate Cells
            for cell in cells:
                cursor.execute("SELECT id FROM regional_cells WHERE name = ?", (cell["name"],))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO regional_cells (name, biome) VALUES (?, ?)", 
                                   (cell["name"], cell["biome"]))
            
            # Hydrate Entities
            for entity in entities:
                cursor.execute("SELECT id FROM entities WHERE name = ?", (entity["name"],))
                if not cursor.fetchone():
                    # 2. Normalization - Assign baseline V12 stats
                    stats = V12_MATRIX.get(entity["type"], {"power": 1, "defense": 1})
                    stat_json = json.dumps(stats)
                    
                    # Assume they start at location 1 for now if no location is specified
                    cursor.execute("INSERT INTO entities (name, type, stat_json, location_id, intent_data) VALUES (?, ?, ?, ?, ?)",
                                   (entity["name"], entity["type"], stat_json, 1, "{}"))
            
            conn.commit()
            print("Ingestion complete. Database hydrated.")
