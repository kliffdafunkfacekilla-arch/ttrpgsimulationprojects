import os
import json
import re
import requests
import sys
import shutil
import sqlite3
import subprocess
import time
import platform

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:latest"
BASE_DIR = os.path.abspath(os.path.join(os.path.expanduser("~"), "Documents", "shatterlands"))
LORE_DB = os.path.join(BASE_DIR, "00_Master_Lore_DB")
FINAL_VAULT = os.path.join(BASE_DIR, "01_Final_Obsidian_Vault")
STATE_FILE = os.path.join(BASE_DIR, "lore_forge_state.json")
DISCOVERED_LORE_FILE = os.path.join(BASE_DIR, "discovered_missing_lore.txt")
ILLUSTRATIONS_DIR = os.path.abspath(os.path.join(os.path.expanduser("~"), "Desktop", "ostraka-wiki", "public", "illustrations"))
ONTOLOGY_FILE = os.path.join(BASE_DIR, "world_ontology.json")

def ensure_ollama():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=1.5)
        if r.status_code == 200:
            return True
    except:
        pass
        
    print("[~] Ollama server not detected. Attempting to start Ollama automatically...")
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["ollama", "serve"], creationflags=0x08000000)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        for _ in range(8):
            time.sleep(1)
            try:
                r = requests.get("http://localhost:11434/api/tags", timeout=1.0)
                if r.status_code == 200:
                    print("[+] Ollama server started successfully!")
                    return True
            except:
                pass
                
        print("[-] Auto-start timed out. Please verify Ollama is installed.")
        return False
    except Exception as e:
        print(f"[-] Failed to auto-start Ollama: {e}")
        return False

def call_ollama(prompt, system="You are an expert lore archivist.", json_mode=False):
    global OLLAMA_MODEL
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False
    }
    if json_mode:
        payload["format"] = "json"
    
    try:
        r = requests.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        return r.json()["response"]
    except Exception as e:
        print(f"[~] Call to model '{OLLAMA_MODEL}' failed: {e}. Trying fallback models...")
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=1.5)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                fallback_options = [m for m in models if m != OLLAMA_MODEL]
                fallback_options.sort(key=lambda x: 0 if "phi" in x.lower() else (1 if "llama" in x.lower() else 2))
                
                for fb_model in fallback_options:
                    print(f"[~] Trying fallback model: {fb_model}")
                    payload["model"] = fb_model
                    try:
                        r = requests.post(OLLAMA_URL, json=payload, timeout=30.0)
                        if r.status_code == 200:
                            OLLAMA_MODEL = fb_model
                            print(f"[+] Fallback model '{fb_model}' succeeded and is now active!")
                            return r.json()["response"]
                    except:
                        pass
        except:
            pass
        raise e

def load_world_config():
    config_path = r"c:\Users\krazy\Desktop\serene-shannon\.worldsmith\config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    print("[!] No world_config.json found. Auto-generating custom configuration...")
    cats = sorted([c for c in os.listdir(LORE_DB) if os.path.isdir(os.path.join(LORE_DB, c))])
    cats = [c for c in cats if "wager" not in c.lower()]
    
    prompt = f"""
    We are building a generalized world-building tool. The user has initialized a directory with the following folders representing their world lore categories:
    {cats}
    
    Suggest a world-building configuration containing:
    1. "world_name": "A suitable name or 'My World'"
    2. "master_timeline": "A short default timeline or description of historical eras"
    3. "timeline_milestones": ["3-5 key milestones that must be documented in their history/timeline notes"]
    4. "category_templates": {{ "category_folder_name": "A short summary of what this section should document" }}
    5. "mandatory_articles": {{ "category_folder_name": ["2-3 essential articles for this category"] }}
    6. "validation_rules": {{
         "cultures_require": ["traditions", "diet"],
         "countries_require": ["capital", "government"],
         "conductors": [],
         "setting_constraints": []
       }}
    
    Respond ONLY in valid JSON.
    """
    ensure_ollama()
    try:
        resp = call_ollama(prompt, json_mode=True)
        config = json.loads(resp)
    except Exception as e:
        config = {
            "world_name": "Generic World",
            "master_timeline": "Genesis -> Ancient Era -> Taiga Era -> Present Day.",
            "timeline_milestones": ["Genesis", "Present Day"],
            "category_templates": {c: "Information about " + c for c in cats},
            "mandatory_articles": {},
            "validation_rules": {
                "cultures_require": ["traditions"],
                "countries_require": ["capital"],
                "conductors": [],
                "setting_constraints": []
            }
        }
        
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved auto-detected configuration to: {config_path}")
    return config

# Load config globally at startup
try:
    CONFIG = load_world_config()
except Exception as e:
    CONFIG = {
        "world_name": "My World",
        "master_timeline": "",
        "timeline_milestones": [],
        "category_templates": {},
        "mandatory_articles": {},
        "validation_rules": {
            "cultures_require": ["traditions"],
            "countries_require": ["capital"],
            "conductors": [],
            "setting_constraints": []
        }
    }

TEMPLATES = CONFIG.get("category_templates", {})
MANDATORY_ARTICLES = CONFIG.get("mandatory_articles", {})
MASTER_TIMELINE = CONFIG.get("master_timeline", "")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed_subjects": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_canon_texts():
    canon_texts = []
    wager_dirs = [d for d in os.listdir(LORE_DB) if os.path.isdir(os.path.join(LORE_DB, d)) and "wager" in d.lower()]
    if wager_dirs:
        wager_dir = os.path.join(LORE_DB, wager_dirs[0])
        for subj in os.listdir(wager_dir):
            subj_dir = os.path.join(wager_dir, subj)
            if os.path.isdir(subj_dir):
                for fname in os.listdir(subj_dir):
                    if fname.endswith(".md"):
                        with open(os.path.join(subj_dir, fname), "r", encoding="utf-8", errors="replace") as f:
                            canon_texts.append(f.read())
    paragraphs = []
    for txt in canon_texts:
        for p in txt.split("\n\n"):
            p = p.strip()
            if len(p) > 20:
                paragraphs.append(p)
    return paragraphs

def extract_canon_benchmark(subject, paragraphs):
    subject_lower = subject.lower()
    matches = [p for p in paragraphs if subject_lower in p.lower()]
    return "\n\n".join(matches)

def find_image_for_subject(subject):
    if not os.path.exists(ILLUSTRATIONS_DIR): return None
    normalized_sub = subject.lower().replace(" ", "_").replace("-", "_")
    if len(normalized_sub) < 4: return None
    for fname in os.listdir(ILLUSTRATIONS_DIR):
        if fname.lower().endswith((".png", ".jpg", ".webp")) and normalized_sub in fname.lower():
            return fname
    return None

def apply_programmatic_backlinks(text, glossary):
    for term in sorted(glossary, key=len, reverse=True):
        if len(term) < 4: continue
        pattern = re.compile(rf'(?<!\[\[)\b({re.escape(term)})\b(?!\]\])', re.IGNORECASE)
        text = pattern.sub(r'[[\1]]', text)
    return text

def gather_raw_text(cat, subj):
    sub_path = os.path.join(LORE_DB, cat, subj)
    raw_parts = []
    if os.path.isdir(sub_path):
        for fname in os.listdir(sub_path):
            if fname.endswith('.md') or fname.endswith('.txt'):
                with open(os.path.join(sub_path, fname), 'r', encoding='utf-8', errors='replace') as f:
                    raw_parts.append(f.read())
    return "\n\n".join(raw_parts)

# --- AI Override and Ignore Comment Stripper Helper ---
def gather_clean_text(cat, subj):
    raw_content = gather_raw_text(cat, subj)
    ai_overrides = []
    
    content_lines = raw_content.splitlines()
    body_content = raw_content
    if len(content_lines) > 0 and content_lines[0].strip() == "---":
        fm_lines = []
        body_start = 0
        for i in range(1, len(content_lines)):
            if content_lines[i].strip() == "---":
                body_start = i + 1
                break
            fm_lines.append(content_lines[i])
            
        for line in fm_lines:
            if ":" in line:
                key, val = line.split(":", 1)
                if key.strip() in ("ai_override", "ai-override"):
                    val = val.strip().strip("[]").replace('"', '').replace("'", "")
                    ai_overrides.extend([x.strip() for x in val.split(",") if x.strip()])
                    
        body_content = "\n".join(content_lines[body_start:])
        
    body_content = re.sub(r"<!--\s*ai-ignore:.*?\s*-->", "", body_content, flags=re.DOTALL)
    body_content = re.sub(r"<!--\s*ai-ignore:start\s*-->.*?<!--\s*ai-ignore:end\s*-->", "", body_content, flags=re.DOTALL)
    
    return body_content, ai_overrides

# --- SQLite Map Database Connection (Decoupled Worldbuilder DB) ---
def get_map_db():
    db_path = r"c:\Users\krazy\Desktop\serene-shannon\lore_forge_world.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    return None

# --- Image Ingestion Engine ---
def ingest_uploaded_image(temp_path, description, subject):
    if not ensure_ollama():
        raise Exception("Ollama server is offline and could not be auto-started.")
    safe_name = subject.lower().replace(" ", "_").replace("-", "_")
    
    prompt = f"""
    We have an image described as: "{description}"
    For the subject: "{subject}"
    Suggest a clean, snake_case filename (including .png, .jpg, or .webp extension depending on the description) for this image.
    Respond ONLY with the filename string, e.g. "avian_capital.png".
    """
    try:
        filename = call_ollama(prompt).strip().replace('"', '').replace("'", "")
        filename = re.sub(r'[^a-zA-Z0-9_\.]', '', filename)
    except:
        filename = f"{safe_name}_illustration.png"
        
    dest_path = os.path.join(ILLUSTRATIONS_DIR, filename)
    os.makedirs(ILLUSTRATIONS_DIR, exist_ok=True)
    shutil.copy2(temp_path, dest_path)
    print(f"[+] Ingested image saved to: {dest_path}")
    
    found_dir = None
    for cat in os.listdir(LORE_DB):
        cat_path = os.path.join(LORE_DB, cat)
        if os.path.isdir(cat_path):
            subj_path = os.path.join(cat_path, subject)
            if os.path.exists(subj_path):
                found_dir = subj_path
                break
                
    if found_dir:
        dictation_path = os.path.join(found_dir, "raw_dictation.md")
        with open(dictation_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n![{description}](/illustrations/{filename})\n")
        print(f"[+] Updated raw note: {dictation_path}")
    return filename

# --- Stage 1: Ontology Synthesis ---
def build_world_ontology(force_rebuild=False):
    print("[~] Building World Ontology...")
    if not ensure_ollama():
        raise Exception("Ollama server is offline and could not be auto-started.")
    
    ontology = {"subjects": {}}
    if os.path.exists(ONTOLOGY_FILE) and not force_rebuild:
        try:
            with open(ONTOLOGY_FILE, "r", encoding="utf-8") as f:
                ontology = json.load(f)
        except:
            ontology = {"subjects": {}}

    cats = sorted([c for c in os.listdir(LORE_DB) if os.path.isdir(os.path.join(LORE_DB, c))])
    cats = [c for c in cats if "wager" not in c.lower()]
    
    for cat in cats:
        cat_path = os.path.join(LORE_DB, cat)
        subjects = sorted([s for s in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, s))])
        for subj in subjects:
            subj_path = os.path.join(cat_path, subj)
            mtime = 0
            for root, dirs, files in os.walk(subj_path):
                for f in files:
                    mtime = max(mtime, os.path.getmtime(os.path.join(root, f)))
            
            cached = ontology["subjects"].get(subj)
            if cached and cached.get("mtime") == mtime and cached.get("category") == cat:
                continue
                
            print(f"  Scanning: {subj} in {cat}...")
            raw_text, overrides = gather_clean_text(cat, subj)
            if not raw_text.strip():
                continue
                
            prompt = f"""
            Analyze the following lore notes for the subject '{subj}' (Category: '{cat}').
            Extract a concise summary (1-2 sentences), key entities mentioned, and list of proper nouns.
            
            Lore Content:
            {raw_text[:5000]}
            
            Respond ONLY in valid JSON format:
            {{
              "summary": "concise summary",
              "entities": ["entity 1", "entity 2"],
              "proper_nouns": ["name 1", "name 2"]
            }}
            """
            try:
                resp = call_ollama(prompt, json_mode=True)
                analysis = json.loads(resp)
                ontology["subjects"][subj] = {
                    "category": cat,
                    "mtime": mtime,
                    "summary": analysis.get("summary", ""),
                    "entities": analysis.get("entities", []),
                    "proper_nouns": analysis.get("proper_nouns", []),
                    "raw_length": len(raw_text)
                }
            except Exception as e:
                print(f"  [-] Failed to analyze {subj}: {e}")
                
    with open(ONTOLOGY_FILE, "w", encoding="utf-8") as f:
        json.dump(ontology, f, ensure_ascii=False, indent=2)
    return ontology

# --- Stage 2: Checklist Validation ---
def validate_world_completeness(ontology, canon_paragraphs):
    print("[~] Running World Completeness Checklist...")
    gaps = []
    errors = []
    
    v_rules = CONFIG.get("validation_rules", {})
    milestones = CONFIG.get("timeline_milestones", [])
    
    # 1. Timeline validation
    for milestone in milestones:
        matched = False
        for subj, data in ontology["subjects"].items():
            if milestone.lower() in subj.lower() or milestone.lower() in data["summary"].lower():
                matched = True
                break
        if not matched:
            gaps.append({
                "category": "Timeline",
                "subject": "World Timeline",
                "field": "milestone",
                "question": f"The milestone '{milestone}' is not clearly documented in any notes. Please write historical notes for it."
            })
            
    # 2. Culture checks
    cultures_require = v_rules.get("cultures_require", [])
    culture_cats = [c for c in TEMPLATES if "culture" in c.lower()]
    for cat in culture_cats:
        subjects = [s for s, d in ontology["subjects"].items() if d["category"] == cat]
        for cult in subjects:
            raw_text, overrides = gather_clean_text(cat, cult)
            raw_text_lower = raw_text.lower()
            for field in cultures_require:
                if field.lower() in overrides:
                    continue
                if field.lower() not in raw_text_lower:
                    gaps.append({
                        "category": cat,
                        "subject": cult,
                        "field": field.lower(),
                        "question": f"Culture '{cult}' lacks documented info about '{field}'. Please describe this aspect."
                    })

    # 3. Country checks
    countries_require = v_rules.get("countries_require", [])
    country_cats = [c for c in TEMPLATES if "country" in c.lower() or "kingdom" in c.lower()]
    for cat in country_cats:
        subjects = [s for s, d in ontology["subjects"].items() if d["category"] == cat]
        for country in subjects:
            raw_text, overrides = gather_clean_text(cat, country)
            raw_text_lower = raw_text.lower()
            for field in countries_require:
                if field.lower() in overrides:
                    continue
                if field.lower() not in raw_text_lower:
                    gaps.append({
                        "category": cat,
                        "subject": country,
                        "field": field.lower(),
                        "question": f"Country/Kingdom '{country}' lacks documented info about '{field}'. Please specify."
                    })

    # 4. Tech / Physics matrix checks
    conductors = v_rules.get("conductors", [])
    for cond in conductors:
        elem = cond.get("element", "").lower()
        absb = cond.get("absorbs", "").lower()
        rels = cond.get("releases", "").lower()
        tech_cats = [c for c in TEMPLATES if "tech" in c.lower() or "magic" in c.lower()]
        for cat in tech_cats:
            subjects = [s for s, d in ontology["subjects"].items() if d["category"] == cat]
            for tech in subjects:
                raw_tech, overrides = gather_clean_text(cat, tech)
                raw_tech_lower = raw_tech.lower()
                if f"conductor_{elem}" in overrides or "conductors" in overrides:
                    continue
                if elem in raw_tech_lower and not (absb in raw_tech_lower and rels in raw_tech_lower):
                    errors.append({
                        "category": cat,
                        "subject": tech,
                        "field": f"conductor_{elem}",
                        "question": f"Conductor rule is inconsistent. In tech/magic setting: '{elem}' must absorb '{absb}' and release '{rels}'."
                    })
                    
    # 5. Database Map Consistency Engine Integration
    conn = get_map_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Map-to-Wiki Factions consistency
            cursor.execute("SELECT name FROM factions")
            map_factions = [row["name"] for row in cursor.fetchall()]
            for mf in map_factions:
                matched = False
                for subj in ontology["subjects"]:
                    if mf.lower() in subj.lower() or subj.lower() in mf.lower():
                        matched = True
                        break
                if not matched:
                    gaps.append({
                        "category": "Map Consistency",
                        "subject": mf,
                        "field": "wiki_article",
                        "question": f"Faction '{mf}' is placed on the map but has no wiki article. Please write one."
                    })
                    
            # Map-to-Wiki Settlements consistency
            cursor.execute("""
                SELECT s.name, g.q, g.r 
                FROM settlements s 
                JOIN global_hexes g ON s.global_hex_id = g.id
            """)
            map_settlements = [{"name": row["name"], "q": row["q"], "r": row["r"]} for row in cursor.fetchall()]
            for ms in map_settlements:
                matched = False
                for subj in ontology["subjects"]:
                    if ms["name"].lower() in subj.lower() or subj.lower() in ms["name"].lower():
                        matched = True
                        break
                if not matched:
                    gaps.append({
                        "category": "Map Consistency",
                        "subject": ms["name"],
                        "field": "wiki_article",
                        "question": f"Settlement '{ms['name']}' is on the map at hex ({ms['q']}, {ms['r']}) but lacks a wiki article. Please write one."
                    })
                    
            # Wiki-to-Map Factions consistency
            wiki_countries = [s for s, d in ontology["subjects"].items() if d["category"] in country_cats]
            for wc in wiki_countries:
                matched = False
                for mf in map_factions:
                    if wc.lower() in mf.lower() or mf.lower() in wc.lower():
                        matched = True
                        break
                if not matched:
                    errors.append({
                        "category": "Map Consistency",
                        "subject": wc,
                        "field": "map_placement",
                        "question": f"Wiki country '{wc}' is documented but does not exist on the map database. Please place it on the map."
                    })
        except Exception as e:
            print(f"[-] Map consistency verification failed: {e}")
        finally:
            conn.close()
            
    # 6. Advanced AI Auditor Consistency Checks (Ollama-driven)
    disabled_linters = CONFIG.get("ai_auditor_settings", {}).get("disabled_linters", [])
    cal_settings = CONFIG.get("calendar_settings", {})
    moons = CONFIG.get("moons", [])
    
    for subj, data in list(ontology["subjects"].items()):
        raw_text, overrides = gather_clean_text(data["category"], subj)
        if "all" in overrides or "consistency" in overrides:
            continue
            
        prompt = f"""
        Analyze the lore text for '{subj}' (Category: '{data["category"]}') against these cosmic settings:
        - Calendar: {cal_settings}
        - Moons: {moons}
        
        Identify any logical contradictions:
        1. Anachronisms: Characters acting before birth or after death.
        2. Mismatched seasons/logistics (e.g. frozen mountain marches described as easy or warm).
        3. Lunar/astrological omens mismatch (e.g. triple dark moon rituals when moons are full/aligned).
        4. Mismatched naming convention drift.
        
        Respond in JSON format:
        {{
          "anachronism": "description of error or null",
          "seasonal_mismatch": "description of error or null",
          "lunar_mismatch": "description of error or null",
          "linguistic_drift": "description of error or null"
        }}
        
        Lore text snippet:
        {raw_text[:2500]}
        """
        try:
            resp = call_ollama(prompt, json_mode=True)
            res = json.loads(resp)
            
            if res.get("anachronism") and "chronological_timeline_gaps" not in disabled_linters:
                if "anachronism" not in overrides:
                    errors.append({
                        "category": data["category"],
                        "subject": subj,
                        "field": "temporal_bounds",
                        "question": f"Temporal Warning: {res['anachronism']}"
                    })
            if res.get("seasonal_mismatch") and "geographical_hydrology_checks" not in disabled_linters:
                if "seasonal_mismatch" not in overrides:
                    errors.append({
                        "category": data["category"],
                        "subject": subj,
                        "field": "climate",
                        "question": f"Seasonal Climate Warning: {res['seasonal_mismatch']}"
                    })
            if res.get("lunar_mismatch") and "atmospheric_buffer_snapping" not in disabled_linters:
                if "lunar_mismatch" not in overrides:
                    errors.append({
                        "category": data["category"],
                        "subject": subj,
                        "field": "astronomy",
                        "question": f"Astrological Inconsistency: {res['lunar_mismatch']}"
                    })
            if res.get("linguistic_drift") and "linguistic_drift" not in disabled_linters:
                if "linguistic_drift" not in overrides:
                    errors.append({
                        "category": data["category"],
                        "subject": subj,
                        "field": "linguistic",
                        "question": f"Linguistic Drift: {res['linguistic_drift']}"
                    })
        except Exception as e:
            print(f"  [-] Advanced linter check failed for {subj}: {e}")
            
    total_checks = len(milestones) + len(gaps) + len(errors)
    if total_checks == 0:
        progress_pct = 100
    else:
        passed_checks = max(0, total_checks - len(gaps) - len(errors))
        progress_pct = int((passed_checks / total_checks) * 100)
    
    return {
        "progress": progress_pct,
        "gaps": gaps,
        "errors": errors
    }

def process_subject_vault(cat, subject, state, canon_paragraphs, global_glossary):
    if subject in state["processed_subjects"]:
        return True
        
    subj_dir = os.path.join(LORE_DB, cat, subject)
    raw_text, overrides = gather_clean_text(cat, subject)
    canon_benchmark = extract_canon_benchmark(subject, canon_paragraphs)
    template = TEMPLATES.get(cat, "No specific template.")
    
    # Locate all map and illustration assets
    safe_name = subject.lower().replace(" ", "_").replace("-", "_")
    image_tags = []
    final_images_dir = os.path.join(FINAL_VAULT, "images")
    os.makedirs(final_images_dir, exist_ok=True)
    
    city_map = f"city_map_{safe_name}.png"
    if os.path.exists(os.path.join(ILLUSTRATIONS_DIR, city_map)):
        shutil.copy2(os.path.join(ILLUSTRATIONS_DIR, city_map), os.path.join(final_images_dir, city_map))
        image_tags.append(f"### City Layout\n![{subject} City Map](../images/{city_map})")
        
    map_crop = f"map_crop_{safe_name}.png"
    if os.path.exists(os.path.join(ILLUSTRATIONS_DIR, map_crop)):
        shutil.copy2(os.path.join(ILLUSTRATIONS_DIR, map_crop), os.path.join(final_images_dir, map_crop))
        image_tags.append(f"### Location Map\n![{subject} Regional Map](../images/{map_crop})")
        
    other_img = find_image_for_subject(subject)
    if other_img and other_img != city_map and other_img != map_crop:
        shutil.copy2(os.path.join(ILLUSTRATIONS_DIR, other_img), os.path.join(final_images_dir, other_img))
        image_tags.append(f"### Illustration\n![{subject} Illustration](../images/{other_img})")
        
    image_md_tag = "\n\n".join(image_tags) if image_tags else ""
    
    generation_prompt = f"""
    Subject: {subject}
    Required Sections: {template}
    
    CANON BENCHMARK:
    {canon_benchmark if canon_benchmark else "None found."}
    
    MASTER HISTORICAL TIMELINE:
    {MASTER_TIMELINE}
    
    RAW LORE:
    {raw_text[:8000]}
    
    Task: Write the definitive, highly-polished Obsidian markdown document for {subject}.
    Follow strict rules:
    1. TONE: ESTEEMED CYNICAL ARCHIVIST.
    2. PRESERVE LORE: Do not lose any flavor text, stories or details.
    3. YAML: Frontmatter at top (aliases, tags, status: final).
    4. IMAGES: Place this exact image markdown block directly under the main title if available:
    {image_md_tag if image_md_tag else "No image available."}
    
    Output ONLY the raw markdown text. No conversational padding or code block markers.
    """
    final_md = call_ollama(generation_prompt)
    if final_md.startswith("```markdown"):
        final_md = final_md.replace("```markdown", "", 1).strip()
    if final_md.startswith("```"):
        final_md = final_md.replace("```", "", 1).strip()
    if final_md.endswith("```"):
        final_md = final_md[:-3].strip()
        
    final_md = apply_programmatic_backlinks(final_md, global_glossary)
    
    out_cat_dir = os.path.join(FINAL_VAULT, cat)
    os.makedirs(out_cat_dir, exist_ok=True)
    out_path = os.path.join(out_cat_dir, f"{subject}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_md)
    print(f"[+] Saved final document: {out_path}")
    state["processed_subjects"].append(subject)
    save_state(state)
    return True

# --- Stage 3: Interactive CLI Loop ---
def main():
    print("===========================================")
    print(f"      LORE FORGE: {CONFIG.get('world_name', 'World')}       ")
    print("===========================================")
    if not ensure_ollama():
        print("[-] Verification failed. Ollama must be running to run the Lore Forge CLI.")
        sys.exit(1)
        
    state = load_state()
    ontology = build_world_ontology()
    canon_paragraphs = load_canon_texts()
    global_glossary = list(ontology["subjects"].keys())
    
    while True:
        status = validate_world_completeness(ontology, canon_paragraphs)
        print(f"\nCompleteness Progress: {status['progress']}%")
        print(f"Active Gaps: {len(status['gaps'])} | Active Errors: {len(status['errors'])}")
        
        problems = status["errors"] + status["gaps"]
        if not problems:
            print("\n[+] Success! Your world is fully documented with no conflicts.")
            ans = input(">> Trigger final generation of Obsidian documents? (y/n/q): ").strip().lower()
            if ans == 'y':
                break
            elif ans in ['n', 'q']:
                sys.exit(0)
                
        print("\nSelect an issue to resolve:")
        for idx, p in enumerate(problems[:10], 1):
            p_type = "ERROR" if p in status["errors"] else "GAP"
            print(f"  {idx}. [{p_type}] {p['subject']} ({p['category']}): {p['question']}")
            
        print("\nOptions:")
        print("  [number] Clarify the specified element")
        print("  [forge]  Trigger compilation of processed notes immediately")
        print("  [rebuild] Force full ontology rebuild")
        print("  [q]      Quit the wizard")
        
        choice = input("\nEnter choice: ").strip().lower()
        if choice == 'q':
            print("Exiting...")
            sys.exit(0)
        elif choice == 'rebuild':
            ontology = build_world_ontology(force_rebuild=True)
        elif choice == 'forge':
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(problems[:10]):
                prob = problems[idx]
                print(f"\nClarifying {prob['subject']} ({prob['category']}):")
                print(f"Question: {prob['question']}")
                answer = input(">> Your Clarification: ").strip()
                if answer.lower() not in ['', 'skip']:
                    subj_dir = os.path.join(LORE_DB, prob['category'], prob['subject'])
                    os.makedirs(subj_dir, exist_ok=True)
                    clar_file = os.path.join(subj_dir, "clarifications.md")
                    with open(clar_file, "a", encoding="utf-8") as f:
                        f.write(f"\n### Clarification ({prob['field']})\n{answer}\n")
                    print("[+] Saved clarification.")
                    ontology = build_world_ontology(force_rebuild=True)
            else:
                print("[-] Invalid index selection.")
        else:
            print("[-] Unrecognized option.")
            
    print("\n[~] Forging Obsidian Vault...")
    cats = sorted([c for c in os.listdir(LORE_DB) if os.path.isdir(os.path.join(LORE_DB, c))])
    cats = [c for c in cats if "wager" not in c.lower()]
    
    for cat in cats:
        cat_path = os.path.join(LORE_DB, cat)
        subjects = sorted([s for s in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, s))])
        for subject in subjects:
            process_subject_vault(cat, subject, state, canon_paragraphs, global_glossary)
            
    print("\n[+] Obsidian vault forged successfully under: 01_Final_Obsidian_Vault!")

if __name__ == "__main__":
    main()
