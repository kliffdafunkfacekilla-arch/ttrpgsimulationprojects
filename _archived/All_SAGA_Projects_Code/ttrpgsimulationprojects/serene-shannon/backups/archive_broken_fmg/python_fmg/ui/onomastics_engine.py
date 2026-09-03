import random
import sqlite3

class OnomasticsEngine:
    def __init__(self, db_path):
        self.db_path = db_path
        self.default_roots = ["Thorg", "Varn", "Kjall", "Ond", "Freyd", "Val", "Bar", "Grom", "Zul", "Tor"]
        self.default_suffixes = ["burg", "fjord", "sted", "heim", "vaag", "grad", "ia", "ton", "field", "dahl"]
        self.ensure_default_profiles()

    def ensure_default_profiles(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we have cultures in FMG database to seed phonetic profiles for
        try:
            cursor.execute("SELECT id, name FROM cultures")
            cultures = cursor.fetchall()
        except sqlite3.OperationalError:
            # Table might not exist or be empty
            cultures = []
            
        # Seed profiles
        for cult in cultures:
            cult_id = str(cult[0])
            name = str(cult[1])
            cursor.execute("SELECT COUNT(*) FROM culture_phonetics WHERE culture_id = ?", (cult_id,))
            if cursor.fetchone()[0] == 0:
                # Custom seed based on culture name
                roots = [name[:4].capitalize(), name[-3:].capitalize() + "o", "Varn", "Kjall", "Ond", "Grom"]
                suffixes = ["burg", "sted", "heim", "grad", "ia"]
                cursor.execute("""
                    INSERT INTO culture_phonetics (culture_id, morpheme_roots, suffix_modifiers, mutator_weight)
                    VALUES (?, ?, ?, ?);
                """, (cult_id, ",".join(roots), ",".join(suffixes), 0.15))
                
        conn.commit()
        conn.close()

    def get_profile(self, culture_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT morpheme_roots, suffix_modifiers, mutator_weight FROM culture_phonetics WHERE culture_id = ?", (str(culture_id),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            roots = row[0].split(",") if row[0] else self.default_roots
            suffixes = row[1].split(",") if row[1] else self.default_suffixes
            weight = row[2] if row[2] is not None else 0.15
            return {"roots": roots, "suffixes": suffixes, "weight": weight}
        return {"roots": self.default_roots, "suffixes": self.default_suffixes, "weight": 0.15}

    def generate_name(self, culture_id, neighbor_culture_id=None, blend_ratio=0.0):
        primary = self.get_profile(culture_id)
        
        # Decide roots and suffixes
        roots = primary["roots"]
        suffixes = primary["suffixes"]
        
        if neighbor_culture_id and blend_ratio > 0.0:
            neighbor = self.get_profile(neighbor_culture_id)
            # Blend root pool
            num_neighbor_roots = int(len(neighbor["roots"]) * blend_ratio)
            blended_roots = roots[:]
            blended_roots.extend(random.sample(neighbor["roots"], min(num_neighbor_roots, len(neighbor["roots"]))))
            
            # Blend suffix pool
            num_neighbor_suffixes = int(len(neighbor["suffixes"]) * blend_ratio)
            blended_suffixes = suffixes[:]
            blended_suffixes.extend(random.sample(neighbor["suffixes"], min(num_neighbor_suffixes, len(neighbor["suffixes"]))))
            
            root = random.choice(blended_roots)
            suffix = random.choice(blended_suffixes)
        else:
            root = random.choice(roots)
            suffix = random.choice(suffixes)
            
        # Syllable mutation based on mutator weight
        weight = primary["weight"]
        if random.random() < weight:
            # Mutate a vowel (e.g. a -> ae, o -> oe)
            vowels = {"a": "ae", "o": "oe", "u": "y", "i": "io", "e": "ea"}
            for v, r in vowels.items():
                if v in root:
                    root = root.replace(v, r, 1)
                    break
                    
        return f"{root}{suffix}"
