import os
import sys
import shutil
import sqlite3
import random
import json
import math
import re
from PyQt6.QtWidgets import (
    QDialog, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, 
    QGroupBox, QTextEdit, QPushButton, QLineEdit, QComboBox, 
    QFormLayout, QFileDialog, QMessageBox, QSlider, QCheckBox, 
    QScrollArea, QListWidget, QStackedWidget, QTreeWidget, QTreeWidgetItem, QSpinBox, QToolBar, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap, QPainter, QBrush, QPen, QFont

# Add workspace directories to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ostraka-wiki", "scripts")))

from python_fmg.ui.main_window import FMGMainWindow
from city_generator import generate_city_map
from python_fmg.config import paths

# Custom Widget for Moon Phases Visualization
class CelestialPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumHeight(160)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Space sky background
        painter.fillRect(self.rect(), QColor("#0C0D14"))
        
        # Draw starry field
        painter.setPen(QColor("#FFFFFF"))
        for i in range(20):
            x = (i * 83 + 27) % max(1, self.width())
            y = (i * 37 + 19) % max(1, self.height())
            painter.drawPoint(x, y)
            
        # Draw moons
        day = self.parent.slider_timeline.value() if self.parent else 2000
        moons = self.parent.worldsmith_config.get("moons", []) if self.parent else []
        
        if not moons:
            painter.setPen(QColor("#5A5F73"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No custom moons configured.")
            return
            
        num_moons = len(moons)
        spacing = self.width() / (num_moons + 1)
        
        for idx, m in enumerate(moons):
            name = m.get("name", "Moon")
            period = float(m.get("orbital_period", 28.0))
            color_hex = m.get("luminescence_color", "#FFFFFF")
            color = QColor(color_hex) if color_hex.startswith("#") else QColor("#FFFFFF")
            
            phase_pct = (day % period) / period
            
            cx = int(spacing * (idx + 1))
            cy = self.height() // 2 - 15
            r = 24
            
            # Shadow backing
            painter.setBrush(QBrush(QColor("#1A1C24")))
            painter.setPen(QPen(QColor("#2C2E3C"), 1))
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            
            # Draw moon light shape based on phase
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            if 0.45 <= phase_pct <= 0.55:
                # Full Moon
                painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            elif phase_pct < 0.05 or phase_pct > 0.95:
                # New Moon (Dash outline)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(color, 1, Qt.PenStyle.DashLine))
                painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            else:
                # Draw crescent overlay
                if phase_pct < 0.5:
                    painter.drawChord(cx - r, cy - r, r * 2, r * 2, -90 * 16, 180 * 16)
                    painter.setBrush(QBrush(QColor("#1A1C24")))
                    painter.drawEllipse(cx - r + int(r * (1 - phase_pct * 2)), cy - r, r * 2, r * 2)
                else:
                    painter.drawChord(cx - r, cy - r, r * 2, r * 2, 90 * 16, 180 * 16)
                    painter.setBrush(QBrush(QColor("#1A1C24")))
                    painter.drawEllipse(cx - r - int(r * ((phase_pct - 0.5) * 2)), cy - r, r * 2, r * 2)
            
            # Label
            painter.setPen(QColor("#A0A5C0"))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(cx - 50, cy + r + 18, 100, 20, Qt.AlignmentFlag.AlignCenter, name)


# Worker Thread for Async Ollama / LLM tasks
class OllamaWorker(QThread):
    finished = pyqtSignal(dict)
    
    def __init__(self, task_type, payload=None):
        super().__init__()
        self.task_type = task_type
        self.payload = payload or {}
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "lore_forge_world.db"))
        
    def run(self):
        try:
            import lore_forge
            
            if self.task_type == "verify":
                lore_forge.ensure_ollama()
                ontology = lore_forge.build_world_ontology(force_rebuild=True)
                canon_paragraphs = lore_forge.load_canon_texts()
                status = lore_forge.validate_world_completeness(ontology, canon_paragraphs)
                self.finished.emit({
                    "success": True, 
                    "task": "verify", 
                    "status": status, 
                    "ontology": ontology
                })
                
            elif self.task_type == "forge":
                lore_forge.ensure_ollama()
                try:
                    import subprocess
                    # Use paths module to locate export script relative to assets
                    export_script = str((paths.ASSETS_DIR / "ostraka pics" / "scripts" / "export_fmg_maps.py"))
                    subprocess.run([sys.executable, export_script], check=True)
                except Exception as ex:
                    print(f"[-] Headless map export error: {ex}")
                    
                state = lore_forge.load_state()
                ontology = lore_forge.build_world_ontology()
                canon_paragraphs = lore_forge.load_canon_texts()
                global_glossary = list(ontology["subjects"].keys())
                
                cats = sorted([c for c in os.listdir(lore_forge.LORE_DB) if os.path.isdir(os.path.join(lore_forge.LORE_DB, c))])
                cats = [c for c in cats if "wager" not in c.lower()]
                
                compiled_files = []
                for cat in cats:
                    cat_path = os.path.join(lore_forge.LORE_DB, cat)
                    subjects = sorted([s for s in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, s))])
                    for subject in subjects:
                        lore_forge.process_subject_vault(cat, subject, state, canon_paragraphs, global_glossary)
                        compiled_files.append(f"{cat}/{subject}.md")
                        
                try:
                    import compile_web_wiki
                    compile_web_wiki.compile_wiki_manifest()
                except Exception as ex:
                    print(f"[-] Web wiki compilation failed: {ex}")
                    
                self.finished.emit({"success": True, "task": "forge", "files": compiled_files})
                
            elif self.task_type == "ingest_image":
                lore_forge.ensure_ollama()
                temp_path = self.payload.get("temp_path")
                description = self.payload.get("description")
                subject = self.payload.get("subject")
                
                filename = lore_forge.ingest_uploaded_image(temp_path, description, subject)
                lore_forge.build_world_ontology(force_rebuild=True)
                self.finished.emit({"success": True, "task": "ingest_image", "filename": filename})
                
            elif self.task_type == "ai_suggest_placements":
                lore_forge.ensure_ollama()
                # Fetch existing factions
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM factions")
                factions = [dict(r) for r in cursor.fetchall()]
                conn.close()
                
                prompt = f"""
                Analyze the following factions: {factions}
                We need to place 3 new key locations (cities/ruins/caves) and suggest natural border placements.
                Suggest placing them at mathematically consistent hex coordinates (q, r between -80 and 80).
                
                Respond ONLY in valid JSON format:
                {{
                  "placements": [
                    {{ "type": "city", "name": "Name", "q": 15, "r": -12, "faction_id": 1, "reason": "Strategic harbor delta" }},
                    {{ "type": "ruins", "name": "Name", "q": -30, "r": 40, "faction_id": null, "reason": "Isolated peak remnants" }}
                  ],
                  "diplomacy": [
                    {{ "faction_a_id": 1, "faction_b_id": 2, "relation": "War", "reason": "Border plain friction" }}
                  ]
                }}
                """
                resp = lore_forge.call_ollama(prompt, json_mode=True)
                self.finished.emit({"success": True, "task": "ai_suggest_placements", "data": json.loads(resp)})
                
            elif self.task_type == "ai_suggest_chronology":
                lore_forge.ensure_ollama()
                notes_text = []
                for root, dirs, files in os.walk(lore_forge.LORE_DB):
                    for f in files:
                        if f.endswith(".md"):
                            with open(os.path.join(root, f), "r", encoding="utf-8", errors="replace") as file_obj:
                                notes_text.append(file_obj.read()[:800])
                                
                prompt = f"""
                Extract historical years, eras, and timeline events mentioned in these notes:
                {notes_text[:15]}
                
                Organize them and return a sorted JSON list of chronological events:
                {{
                  "events": [
                    {{ "year": 412, "name": "The Great Siege", "description": "Breached from within.", "q": 0, "r": 0 }},
                    {{ "year": 1200, "name": "Aether Collapse", "description": "Luminosity cycle shift.", "q": 15, "r": -12 }}
                  ]
                }}
                """
                resp = lore_forge.call_ollama(prompt, json_mode=True)
                self.finished.emit({"success": True, "task": "ai_suggest_chronology", "data": json.loads(resp)})
                
            elif self.task_type == "ai_suggest_cosmology":
                lore_forge.ensure_ollama()
                prompt = """
                Suggest mathematically stable, consistent calendar settings and moon orbital periods.
                Year length should divide evenly with months. Moons should avoid orbital frequency collisions.
                
                Respond ONLY in valid JSON format:
                {{
                  "calendar_settings": {{
                    "months_per_year": 12,
                    "days_per_month": 30,
                    "leap_days": 5
                  }},
                  "moons": [
                    {{ "name": "Selene", "orbital_period": 28.0, "luminescence_color": "#FFFFFF", "tidal_modifier": 1.0 }},
                    {{ "name": "Malakor", "orbital_period": 8.0, "luminescence_color": "#48AA56", "tidal_modifier": 1.5 }}
                  ]
                }}
                """
                resp = lore_forge.call_ollama(prompt, json_mode=True)
                self.finished.emit({"success": True, "task": "ai_suggest_cosmology", "data": json.loads(resp)})
                
            elif self.task_type == "ai_advise":
                lore_forge.ensure_ollama()
                ontology = lore_forge.build_world_ontology()
                prompt = f"""
                Analyze the following worldbuilding ontology:
                {json.dumps(ontology, indent=2)[:3000]}
                
                Provide a structured narrative designer analysis for the writer:
                1. Identify missing elements (e.g. Factions lacking leaders, key settlements lacking historical origin, missing magic rules).
                2. Suggest 3 concrete new lore notes (names and descriptions) to write next to make the world fully realized.
                3. Suggest 2 major historical event timeline milestones to resolve chronicle gaps.
                
                Keep suggestions tailored to setting constraints (no humans, animal-kin, fantasy/arcane tech).
                """
                resp = lore_forge.call_ollama(prompt)
                self.finished.emit({"success": True, "task": "ai_advise", "response": resp})
                
            elif self.task_type == "ai_resolve":
                lore_forge.ensure_ollama()
                issue_subject = self.payload.get("subject")
                issue_desc = self.payload.get("description")
                prompt = f"""
                You are a narrative designer. The writer has an issue/gap in their world:
                Subject: {issue_subject}
                Issue: {issue_desc}
                
                Draft a creative, brief (1-2 paragraph) resolution explaining this lore gap. 
                Ensure it conforms to the setting constraints (no humans, animal-kin, arcane/leylines elements).
                """
                resp = lore_forge.call_ollama(prompt)
                self.finished.emit({"success": True, "task": "ai_resolve", "response": resp})
                
            elif self.task_type == "ai_classify_note":
                lore_forge.ensure_ollama()
                note_text = self.payload.get("text", "")
                categories = ["people", "culture/species", "faction", "state(country)", "religion", "cosmology/rules", "arcana/tech", "magic/power", "location", "history", "object/item", "flora", "fauna", "goods", "relics/valuables"]
                prompt = f"""
                Classify this text into exactly one of the following categories:
                {categories}
                
                Respond ONLY with the category name itself (all lowercase, no punctuation).
                Text:
                {note_text[:2000]}
                """
                resp = lore_forge.call_ollama(prompt).strip().lower()
                matched = next((c for c in categories if c in resp), "people")
                self.finished.emit({"success": True, "task": "ai_classify_note", "category": matched})
                
            elif self.task_type == "ai_suggest_inquiries":
                lore_forge.ensure_ollama()
                note_text = self.payload.get("text", "")
                note_title = self.payload.get("title", "")
                prompt = f"""
                You are a narrative designer. Analyze this worldbuilding lore note:
                Title: {note_title}
                Content:
                {note_text[:2000]}
                
                Suggest 2-3 brief, engaging questions to help the writer develop this lore further and check for any gaps or inconsistencies.
                Respond with a clean bulleted list of 2-3 questions. Do not write any other intro/outro text.
                """
                resp = lore_forge.call_ollama(prompt)
                self.finished.emit({"success": True, "task": "ai_suggest_inquiries", "response": resp})
                
            elif self.task_type == "ai_chat":
                lore_forge.ensure_ollama()
                prompt_txt = self.payload.get("prompt")
                
                ontology = lore_forge.build_world_ontology()
                
                sys_prompt = f"""
                You are the Ostraka Worldsmith AI Assistant. Your primary goal is to help the writer build their world by abstracting all technical details (JSON configs, database records, markdown scaffolding) through a friendly conversational interface.

                Active World Ontology:
                {json.dumps(ontology, indent=2)[:1500]}

                Guidelines:
                1. If the user wants to create or update something (e.g. a faction, location, event, moon, calendar setting), check if you have all the required details. If not, ask the user 1-2 simple questions in "chat_response" to collect them.
                2. Once you have enough information, perform the abstraction:
                   - To draft or update a lore note: Provide "draft_note" with "title" (snake_case) and "content" (markdown text).
                   - To insert/update the database: Provide "db_action" with "action" ("insert" or "update"), "table" ("factions", "settlements", "chronology_events", or "markers"), and "data" (key-value dictionary).
                     - Factions: "name" (string)
                     - Settlements: "name" (string), "global_hex_id" (int), "faction_id" (int)
                     - Chronology Events: "year" (int), "end_year" (int), "name" (string), "description" (string), "global_q" (int), "global_r" (int)
                     - Markers: "type" (string: RUINS/DUNGEON/CAVE/PORTAL/OBELISK), "global_hex_id" (int), "name" (string)
                   - To update calendar or moons: Provide "config_action" with "calendar_settings" (dict) or "moons" (list of dicts).
                3. If they just ask general questions, respond in "chat_response" and leave other action keys null.
                4. Keep the Ostraka constraints (no humans, animal-kin, fantasy/arcane setting).

                You MUST respond ONLY in valid JSON conforming to this schema:
                {{
                  "chat_response": "Your friendly conversational response or follow-up question here.",
                  "draft_note": {{
                    "title": "note_filename_without_extension",
                    "content": "# Markdown content here..."
                  }} or null,
                  "db_action": {{
                    "action": "insert",
                    "table": "factions",
                    "data": {{ "name": "Faction Name" }}
                  }} or null,
                  "config_action": {{
                    "calendar_settings": {{ "months_per_year": 12, "days_per_month": 30, "leap_days": 5 }},
                    "moons": [
                      {{ "name": "Selene", "orbital_period": 28.0, "luminescence_color": "#FFFFFF" }}
                    ]
                  }} or null
                }}

                User prompt: {prompt_txt}
                """
                resp = lore_forge.call_ollama(sys_prompt, json_mode=True)
                self.finished.emit({"success": True, "task": "ai_chat", "response": resp})
                
        except Exception as e:
            self.finished.emit({"success": False, "task": self.task_type, "error": str(e)})


# Worker Thread for Reverse Cartography Batch Importer
class ReverseCartographyWorker(QThread):
    finished = pyqtSignal(dict)
    
    def __init__(self, folder_path, db_path):
        super().__init__()
        self.folder_path = folder_path
        self.db_path = db_path
        
    def run(self):
        try:
            import lore_forge
            import random
            from python_fmg.core.grid import get_neighbors
            lore_forge.ensure_ollama()
            
            imported_files = []
            extracted_data = []
            
            for root, dirs, files in os.walk(self.folder_path):
                for f in files:
                    if f.endswith((".md", ".txt")):
                        fpath = os.path.join(root, f)
                        with open(fpath, "r", encoding="utf-8", errors="replace") as file_obj:
                            content = file_obj.read()
                            
                        prompt = f"""
                        Analyze this worldbuilding lore text:
                        {content[:2000]}
                        
                        Extract:
                        1. Names of cities/keeps/settlements
                        2. Names of mountain ranges, deserts, or rivers
                        3. Description/climate of those features or regions (e.g. coastal, frozen, desert, high peaks, subterranean)
                        
                        Respond ONLY in valid JSON:
                        {{
                          "settlements": [{{"name": "Name", "description": "coastal/mountain/underground/etc"}}],
                          "geography": [{{"name": "Name", "type": "mountain/desert/river", "climate": "frozen/arid/standard"}}]
                        }}
                        """
                        resp = lore_forge.call_ollama(prompt, json_mode=True)
                        extracted = json.loads(resp)
                        
                        # Copy file to master DB
                        target_dir = os.path.join(lore_forge.LORE_DB, "unclassified", f.replace(".md", "").replace(".txt", ""))
                        os.makedirs(target_dir, exist_ok=True)
                        shutil.copy2(fpath, os.path.join(target_dir, f))
                        
                        imported_files.append(f)
                        extracted_data.append((f, extracted))
            
            # Map generation heuristics based on extracted tags
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for f, ext in extracted_data:
                for sett in ext.get("settlements", []):
                    name = sett["name"]
                    desc = sett["description"].lower()
                    
                    # Target hex selection
                    cursor.execute("SELECT id, q, r, elevation, biome FROM global_hexes")
                    all_hexes = cursor.fetchall()
                    
                    def is_coastal(q, r):
                        for nq, nr in get_neighbors(q, r):
                            cursor.execute("SELECT elevation FROM global_hexes WHERE q=? AND r=?", (nq, nr))
                            row = cursor.fetchone()
                            if row and row[0] < 3: return True
                        return False
                        
                    candidate_hexes = []
                    for hex_id, hq, hr, elev, biome in all_hexes:
                        score = 0
                        # Check existing settlements
                        cursor.execute("SELECT id FROM settlements WHERE global_hex_id = ?", (hex_id,))
                        if cursor.fetchone(): continue
                        
                        if elev >= 3: # Land only
                            if "mountain" in desc and elev >= 10: score += 10
                            elif "coastal" in desc and is_coastal(hq, hr): score += 10
                            elif "underground" in desc and biome == 13: score += 10
                            elif "desert" in desc and biome == 3: score += 10
                            elif biome == 4: score += 2 # plains fallback
                            candidate_hexes.append((score, hex_id))
                            
                    if candidate_hexes:
                        candidate_hexes.sort(reverse=True)
                        best_hex = candidate_hexes[0][1]
                        
                        # Insert settlement
                        cursor.execute("""
                            INSERT INTO settlements (name, global_hex_id, settlement_level, faction_id)
                            VALUES (?, ?, 2, 1)
                        """, (name, best_hex))
                        
            conn.commit()
            conn.close()
            self.finished.emit({"success": True, "count": len(imported_files)})
        except Exception as e:
            self.finished.emit({"success": False, "error": str(e)})


# Dialogs
class StartupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Worldsmith Sandbox Setup")
        self.setMinimumSize(420, 240)
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("<h3>Worldsmith Lore Forge Sandbox</h3>")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel("An advanced procedurally generated fantasy map editor, timeline chronologist, and cosmic simulator.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_desc)
        
        btn_box = QHBoxLayout()
        self.btn_new = QPushButton("Forge New World")
        self.btn_load = QPushButton("Load Active World")
        
        self.btn_new.clicked.connect(self.on_new)
        self.btn_load.clicked.connect(self.on_load)
        
        btn_box.addWidget(self.btn_new)
        btn_box.addWidget(self.btn_load)
        layout.addLayout(btn_box)
        layout.addStretch()
        
    def on_new(self):
        self.result_action = "new"
        self.accept()
        
    def on_load(self):
        self.result_action = "load"
        self.accept()
        
class FreshWorldPromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Start Fresh World")
        self.setMinimumSize(400, 300)
        
        layout = QFormLayout(self)
        
        self.txt_name = QLineEdit("Ostraka")
        layout.addRow("World Name:", self.txt_name)
        
        self.txt_eras = QLineEdit("Dawn Era -> Age of Magic -> Present Day")
        layout.addRow("Historical Eras:", self.txt_eras)
        
        self.txt_milestones = QLineEdit("The Shattered Rift, Great Alignment")
        layout.addRow("Timeline Milestones (comma separated):", self.txt_milestones)
        
        self.btn_submit = QPushButton("Forge World Database")
        self.btn_submit.clicked.connect(self.accept)
        layout.addRow(self.btn_submit)


# Dedicated Lore Book & AI Writer Companion Separate Window
class LoreBookAIWriterWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 Lore Book & AI Narrative Writer Companion")
        self.setMinimumSize(950, 700)
        self.parent = parent
        self.db_path = parent.db_path if parent else None
        
        # Companion Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #0E0F14;
            }
            QLabel {
                color: #A0A5B5;
                font-weight: bold;
            }
            QTextEdit, QLineEdit, QComboBox {
                background-color: #16171E;
                border: 1px solid #232530;
                color: #E2E8F0;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
        """)
        
        main_lay = QVBoxLayout(self)
        
        # Horizontal Splitter for Reader and Editor
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 1. Left Panel: Viewing Panel
        left_widget = QWidget()
        left_lay = QVBoxLayout(left_widget)
        left_lay.setContentsMargins(0, 0, 0, 0)
        
        left_lay.addWidget(QLabel("📖 Vault Note Reader (Read-Only)"))
        self.cb_notes = QComboBox()
        self.cb_notes.currentIndexChanged.connect(self.on_note_selected)
        left_lay.addWidget(self.cb_notes)
        
        self.view_panel = QTextEdit()
        self.view_panel.setReadOnly(True)
        self.view_panel.setPlaceholderText("Select a note from the library above to read...")
        left_lay.addWidget(self.view_panel)
        h_splitter.addWidget(left_widget)
        
        # 2. Right Panel: Notepad
        right_widget = QWidget()
        right_lay = QVBoxLayout(right_widget)
        right_lay.setContentsMargins(0, 0, 0, 0)
        
        right_lay.addWidget(QLabel("✍️ Notepad (Writer / Editor)"))
        self.txt_note_title = QLineEdit()
        self.txt_note_title.setPlaceholderText("New Note Title (e.g. Shadow_Rift_Eruptions)")
        right_lay.addWidget(self.txt_note_title)
        
        self.notepad = QTextEdit()
        self.notepad.setPlaceholderText("Draft new lore notes here. You can copy AI suggestions or write from scratch...")
        right_lay.addWidget(self.notepad)
        
        btn_lay = QHBoxLayout()
        self.btn_clear = QPushButton("Clear Notepad / New Note")
        self.btn_clear.clicked.connect(self.on_clear_note)
        self.btn_save = QPushButton("Save Notepad to Vault")
        self.btn_save.clicked.connect(self.on_save_note)
        btn_lay.addWidget(self.btn_clear)
        btn_lay.addWidget(self.btn_save)
        right_lay.addLayout(btn_lay)
        h_splitter.addWidget(right_widget)
        
        main_lay.addWidget(h_splitter, 3)
        
        # 3. Bottom Panel: AI Chat Prompt Panel
        chat_box = QGroupBox("🤖 Narrative AI Lore Chat Logic Board")
        chat_box.setStyleSheet("QGroupBox { border: 1px solid #232530; border-radius: 6px; padding-top: 10px; background-color: #12131A; }")
        chat_lay = QVBoxLayout(chat_box)
        
        self.txt_chat_history = QTextEdit()
        self.txt_chat_history.setReadOnly(True)
        self.txt_chat_history.setMaximumHeight(140)
        self.txt_chat_history.setPlaceholderText("Ask the AI Writer about Ostraka's history, species makeup, or request drafts for missing notes...")
        chat_lay.addWidget(self.txt_chat_history)
        
        prompt_lay = QHBoxLayout()
        self.txt_prompt = QLineEdit()
        self.txt_prompt.setPlaceholderText("Ask the AI about your world, check canon violations, or prompt custom drafts...")
        self.txt_prompt.returnPressed.connect(self.send_chat_to_ai)
        self.btn_send_chat = QPushButton("Send Prompt")
        self.btn_send_chat.clicked.connect(self.send_chat_to_ai)
        prompt_lay.addWidget(self.txt_prompt)
        prompt_lay.addWidget(self.btn_send_chat)
        chat_lay.addLayout(prompt_lay)
        
        main_lay.addWidget(chat_box, 2)
        
        self.refresh_notes_list()
        
    def refresh_notes_list(self):
        import lore_forge
        self.cb_notes.blockSignals(True)
        self.cb_notes.clear()
        self.cb_notes.addItem("Select note to view...", None)
        
        if os.path.exists(lore_forge.LORE_DB):
            for root, dirs, files in os.walk(lore_forge.LORE_DB):
                for f in files:
                    if f.endswith(".md"):
                        rel_path = os.path.relpath(os.path.join(root, f), lore_forge.LORE_DB)
                        display_name = rel_path.replace("\\", "/").replace(".md", "")
                        self.cb_notes.addItem(display_name, os.path.join(root, f))
        self.cb_notes.blockSignals(False)

    def on_note_selected(self, idx):
        file_path = self.cb_notes.itemData(idx)
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.view_panel.setPlainText(content)
            
            # Auto-populate Notepad for editing
            name = os.path.basename(file_path).replace(".md", "")
            self.txt_note_title.setText(name)
            self.notepad.setPlainText(content)
            self.active_edit_path = file_path
        else:
            self.view_panel.clear()
            self.txt_note_title.clear()
            self.notepad.clear()
            self.active_edit_path = None

    def on_clear_note(self):
        self.txt_note_title.clear()
        self.notepad.clear()
        self.active_edit_path = None
        self.cb_notes.setCurrentIndex(0)

    def on_save_note(self):
        title = self.txt_note_title.text().strip()
        content = self.notepad.toPlainText().strip()
        if not title:
            QMessageBox.warning(self, "Title Required", "Please enter a note title.")
            return
            
        import lore_forge
        if hasattr(self, "active_edit_path") and self.active_edit_path:
            save_path = self.active_edit_path
        else:
            subj_dir = os.path.join(lore_forge.LORE_DB, "unclassified", title)
            os.makedirs(subj_dir, exist_ok=True)
            save_path = os.path.join(subj_dir, f"{title}.md")
            
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Saved", f"Note '{title}' saved successfully!")
            self.refresh_notes_list()
            if self.parent:
                self.parent.refresh_notes_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save note: {e}")

    def send_chat_to_ai(self):
        prompt = self.txt_prompt.text().strip()
        if not prompt:
            return
            
        self.txt_chat_history.append(f"<b>You:</b> {prompt}")
        self.txt_prompt.clear()
        
        self.txt_chat_history.append("<i>AI is thinking...</i>")
        self.btn_send_chat.setEnabled(False)
        
        if self.parent:
            self.chat_worker = self.parent.start_ai_task("ai_chat", {"prompt": prompt})
            self.chat_worker.finished.connect(self.on_ai_chat_finished)
        else:
            self.txt_chat_history.append("<b>AI:</b> Error: Parent context is missing.")
            self.btn_send_chat.setEnabled(True)

    def on_ai_chat_finished(self, result):
        self.btn_send_chat.setEnabled(True)
        # Remove thinking prompt
        history = self.txt_chat_history.toHtml()
        history = history.replace("<i>AI is thinking...</i>", "")
        self.txt_chat_history.setHtml(history)
        
        if result.get("success"):
            try:
                data = json.loads(result["response"])
            except Exception as e:
                # Fallback if AI didn't return valid JSON
                self.txt_chat_history.append(f"<b>AI:</b> {result['response']}<br>")
                return
                
            resp = data.get("chat_response", "")
            self.txt_chat_history.append(f"<b>AI:</b> {resp}<br>")
            
            # 1. Draft Note abstraction
            draft = data.get("draft_note")
            if draft and isinstance(draft, dict):
                title = draft.get("title", "")
                content = draft.get("content", "")
                if title and content:
                    self.txt_note_title.setText(title)
                    self.notepad.setPlainText(content)
                    self.txt_chat_history.append("<i>[AI Note Drafted: Loaded into your notepad on the right]</i><br>")
                    
            # 2. Database Action abstraction
            db_act = data.get("db_action")
            if db_act and isinstance(db_act, dict):
                action = db_act.get("action")
                table = db_act.get("table")
                row_data = db_act.get("data")
                if action == "insert" and table and row_data:
                    try:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        
                        cols = ", ".join(row_data.keys())
                        placeholders = ", ".join(["?"] * len(row_data))
                        vals = tuple(row_data.values())
                        
                        query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
                        cursor.execute(query, vals)
                        conn.commit()
                        conn.close()
                        
                        self.txt_chat_history.append(f"<i>[AI DB Action: Inserted record into {table} successfully]</i><br>")
                        if self.parent:
                            self.parent.load_db()
                    except Exception as sql_ex:
                        self.txt_chat_history.append(f"<i>[AI DB Error: {sql_ex}]</i><br>")
                        
            # 3. Config Action abstraction
            cfg_act = data.get("config_action")
            if cfg_act and isinstance(cfg_act, dict) and self.parent:
                cal = cfg_act.get("calendar_settings")
                moons = cfg_act.get("moons")
                updated = False
                if cal:
                    self.parent.worldsmith_config["calendar_settings"] = cal
                    updated = True
                if moons:
                    self.parent.worldsmith_config["moons"] = moons
                    updated = True
                if updated:
                    self.parent.save_worldsmith_config()
                    self.parent.celestial_preview.update()
                    self.parent.check_lunar_conjunctions()
                    self.txt_chat_history.append("<i>[AI Config Action: Celestial settings updated in config.json]</i><br>")
        else:
            self.txt_chat_history.append(f"<b>AI:</b> Failed to generate response: {result.get('error')}<br>")


# Main Window Class
class LoreForgeMainWindow(FMGMainWindow):
    def __init__(self):
        super().__init__()
        
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "lore_forge_world.db"))
        sim_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shatterlands_simulator", "core_engine", "world_state.db"))
        self.worldsmith_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".worldsmith"))
        self.config_file = os.path.join(self.worldsmith_dir, "config.json")
        
        os.makedirs(self.worldsmith_dir, exist_ok=True)
        self.load_worldsmith_config()
        
        # Startup Dialog Flow
        dlg = StartupDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.result_action == "load":
                if not os.path.exists(self.db_path) and os.path.exists(sim_db_path):
                    try:
                        shutil.copy2(sim_db_path, self.db_path)
                    except Exception as e:
                        print(f"[-] Initial db copy failed: {e}")
                self.load_db()
            elif dlg.result_action == "new":
                self.trigger_new_world_flow()
        else:
            sys.exit(0)
            
        self.active_problems = []
        self.current_worker = None
        self.current_city_name = None
        self.current_city_seed = None
        self.current_note_path = None
        
        # Style Sheet
        self.setStyleSheet("""
            QWidget {
                background-color: #111216;
                color: #E2E8F0;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                border: 1px solid #1E202B;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                padding: 10px;
                background-color: #16171E;
            }
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
            QPushButton:disabled {
                background-color: #2E303F;
                color: #64748B;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #1C1D24;
                border: 1px solid #2A2D3A;
                border-radius: 4px;
                padding: 5px;
                color: #F1F5F9;
            }
            QHeaderView::section {
                background-color: #1C1D24;
                color: #E2E8F0;
                border: 1px solid #2A2D3A;
                padding: 4px;
            }
            QTableWidget, QTreeWidget {
                gridline-color: #2A2D3A;
                background-color: #121318;
                border: 1px solid #2A2D3A;
            }
            QProgressBar {
                border: 1px solid #2A2D3A;
                border-radius: 4px;
                text-align: center;
                height: 20px;
                background-color: #1C1D24;
            }
            QProgressBar::chunk {
                background-color: #6366F1;
            }
        """)

        self.setup_lore_forge_panel()
        
        # Connect Hover & Highlight events on map to Bottom Inspector Display
        self.map_viewer.hex_hovered.connect(self.update_inspect_display)
        self.map_viewer.hex_selected.connect(self.update_inspect_display)
        
        self.run_verification()
        
    def on_culture_names_changed(self):
        """
        Handler for the editingFinished signal of the base language template
        QLineEdit in NameStyleEditorDialog. Stores the template into the
        worldsmith config and persists it.
        """
        try:
            template = self.txt_base_lang.text().strip()
            self.worldsmith_config["base_lang_template"] = template
            self.save_worldsmith_config()
            self.txt_chat_history.append("<i>[Info] Culture naming template updated.</i><br>")
        except Exception as exc:
            self.txt_chat_history.append(f"<i>[Error] Failed to update culture naming: {exc}</i><br>")
    
    def load_worldsmith_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.worldsmith_config = json.load(f)
            except:
                self.worldsmith_config = self.get_default_config()
        else:
            self.worldsmith_config = self.get_default_config()
            self.save_worldsmith_config()
            
    def get_default_config(self):
        return {
            "wind_bands": [
                {"pct_max": 0.14, "dir": "SW"},
                {"pct_max": 0.43, "dir": "NE"},
                {"pct_max": 0.57, "dir": "SW"},
                {"pct_max": 0.71, "dir": "NW"},
                {"pct_max": 1.00, "dir": "NE"}
            ],
            "vault_settings": {
                "world_name": "Ostraka",
                "active_modules": {
                    "climate_simulation": True,
                    "ocean_currents": True,
                    "custom_calendar": True,
                    "astronomical_spheres": True,
                    "crime_underworld": True
                }
            },
            "calendar_settings": {
                "months_per_year": 12,
                "days_per_month": 30,
                "leap_days": 5
            },
            "moons": [
                {"name": "Selene", "orbital_period": 28.0, "luminescence_color": "#FFFFFF", "tidal_modifier": 1.0},
                {"name": "Malakor", "orbital_period": 5.5, "luminescence_color": "#48AA56", "tidal_modifier": 1.8}
            ],
            "unreliable_narrators": [
                {
                    "profile_id": "church_inquisition",
                    "display_name": "Imperial Inquisition",
                    "name_overrides": {
                        "Shattered Rift": "Devil's Basin",
                        "Sorax": "Blighted Hold"
                    }
                }
            ],
            "custom_layers": [
                {
                    "layer_id": "usr_lay_dream_realm",
                    "name": "The Dream-Realm",
                    "type": "polygon_overlay",
                    "attributes": ["sanity_drain_int", "deity_doc_id"]
                }
            ],
            "custom_templates": {
                "superpower": [
                    {"fieldName": "power_class", "fieldType": "string", "isRequired": True},
                    {"fieldName": "arcane_catalyst", "fieldType": "document_link", "isRequired": False},
                    {"fieldName": "collateral_damage_risk", "fieldType": "number", "isRequired": True}
                ]
            },
            "ai_auditor_settings": {
                "strictness_mode": "permissive",
                "disabled_linators": []
            }
        }
        
    def save_worldsmith_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.worldsmith_config, f, indent=2)
        except Exception as e:
            print(f"[-] Failed to save worldsmith config: {e}")
            
    def save_wind_bands_config(self):
        try:
            bands = json.loads(self.txt_wind_bands.toPlainText())
            if not isinstance(bands, list):
                raise ValueError("Must be a JSON List.")
            self.worldsmith_config["wind_bands"] = bands
            self.save_worldsmith_config()
            QMessageBox.information(self, "Success", "Custom wind bands saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Failed to save wind bands: {e}")
            
    def save_calendar_settings(self):
        try:
            cal = json.loads(self.txt_calendar_config.toPlainText())
            self.worldsmith_config["calendar_settings"] = cal
            self.save_worldsmith_config()
            QMessageBox.information(self, "Success", "Calendar settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Failed to save calendar: {e}")

    def save_moons_settings(self):
        try:
            moons = []
            for r in range(self.table_moons.rowCount()):
                name = self.table_moons.item(r, 0).text().strip()
                period = float(self.table_moons.item(r, 1).text().strip())
                color = self.table_moons.item(r, 2).text().strip()
                moons.append({
                    "name": name,
                    "orbital_period": period,
                    "luminescence_color": color,
                    "tidal_modifier": 1.0
                })
            self.worldsmith_config["moons"] = moons
            self.save_worldsmith_config()
            self.check_lunar_conjunctions()
            self.celestial_preview.update()
            QMessageBox.information(self, "Success", "Moons list saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Invalid Inputs", f"Failed to save moons: {e}")

    def save_narrators_settings(self):
        try:
            narrators = json.loads(self.txt_narrators_config.toPlainText())
            self.worldsmith_config["unreliable_narrators"] = narrators
            self.save_worldsmith_config()
            
            # Refresh combobox
            self.cb_narrator.clear()
            self.cb_narrator.addItem("Objective Reality", None)
            for n in narrators:
                self.cb_narrator.addItem(n["display_name"], n["profile_id"])
                
            QMessageBox.information(self, "Success", "Narrators list saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Failed to save narrators: {e}")
            
    def trigger_new_world_flow(self):
        reply = QMessageBox.question(
            self, 
            "Setup New World", 
            "Would you like to import an unstructured folder of notes (Reverse Cartography) to seed the map?\n\nClick 'Yes' to import or 'No' to start fresh.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.run_reverse_cartography()
        else:
            self.trigger_fresh_world_prompts()
            
    def trigger_fresh_world_prompts(self):
        dlg = FreshWorldPromptDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            w_name = dlg.txt_name.text().strip()
            eras = dlg.txt_eras.text().strip()
            milestones = [m.strip() for m in dlg.txt_milestones.text().split(",") if m.strip()]
            
            self.worldsmith_config["vault_settings"]["world_name"] = w_name
            self.worldsmith_config["vault_settings"]["master_timeline"] = eras
            self.worldsmith_config["timeline_milestones"] = milestones
            self.save_worldsmith_config()
            
            from python_fmg.core.generators import generate_world
            self.state = generate_world(R=110, elevation_seed=random.randint(1, 100000))
            
            from python_fmg.core.db_sync import save_to_db
            from python_fmg.ui.update_db_schema import update_schema
            update_schema()
            
            save_to_db(self.state, self.db_path)
            self.map_viewer.load_map(self.state)
            self.statusBar().showMessage(f"Fresh world '{w_name}' initialized successfully!")

    def start_ai_task(self, task_type, payload=None):
        worker = OllamaWorker(task_type, payload)
        worker.finished.connect(worker.deleteLater)
        worker.start()
        return worker

    def ask_ai_to_draft_resolution(self):
        selected = self.gaps_table.selectedItems()
        if not selected or len(selected) < 3:
            return
        subject = selected[0].text()
        desc = selected[2].text()
        
        self.text_resolve_answer.setPlainText("AI is drafting a resolution... Please wait...")
        self.btn_ai_draft.setEnabled(False)
        
        self.draft_worker = self.start_ai_task("ai_resolve", {"subject": subject, "description": desc})
        self.draft_worker.finished.connect(self.on_ai_draft_finished)
        
    def on_ai_draft_finished(self, result):
        self.btn_ai_draft.setEnabled(True)
        if result.get("success"):
            self.text_resolve_answer.setPlainText(result["response"])
        else:
            self.text_resolve_answer.setPlainText(f"AI Drafting failed: {result.get('error')}")

    def setup_lore_forge_panel(self):
        self.right_dock = QDockWidget("Lore Forge Panel", self)
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.right_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.right_dock.setMinimumWidth(400)
        self.right_dock.setMaximumWidth(600)
        
        # Right Stacked Widget
        self.stacked_widget = QStackedWidget()
        self.right_dock.setWidget(self.stacked_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)
        
        # Bottom screen Cell Inspector Dock setup
        self.bottom_dock = QDockWidget("Highlighted Cell Inspector Dashboard", self)
        self.bottom_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.bottom_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.bottom_dock.setMinimumHeight(70)
        self.bottom_dock.setMaximumHeight(100)
        
        bottom_container = QWidget()
        bottom_lay = QHBoxLayout(bottom_container)
        bottom_lay.setContentsMargins(15, 4, 15, 4)
        
        self.lbl_inspect_coords = QLabel("<b>Coords:</b> N/A")
        self.lbl_inspect_terrain = QLabel("<b>Terrain:</b> N/A")
        self.lbl_inspect_settlement = QLabel("<b>Settlement:</b> N/A")
        self.lbl_inspect_magic = QLabel("<b>Magic & Anomaly:</b> N/A")
        self.lbl_inspect_garrison = QLabel("<b>Garrison:</b> N/A")
        
        for lbl in [self.lbl_inspect_coords, self.lbl_inspect_terrain, self.lbl_inspect_settlement, self.lbl_inspect_magic, self.lbl_inspect_garrison]:
            lbl.setStyleSheet("font-size: 12px; color: #E2E8F0;")
            bottom_lay.addWidget(lbl)
            
        self.bottom_dock.setWidget(bottom_container)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)
        
        # Instantiate base dialogs as embedded widgets
        from python_fmg.ui.main_window import (
            ElevationEditorDialog, BiomesEditorDialog, FactionsEditorDialog,
            ParagonsEditorDialog, ChaosPathsEditorDialog, FringeGroupsEditorDialog,
            ChaosEditorDialog, SettlementsEditorDialog, NameStyleEditorDialog,
            MarkersEditorDialog, ForcesEditorDialog, RoutesEditorDialog
        )
        
        self.dialog_elevation = ElevationEditorDialog(self)
        self.dialog_elevation.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_biomes = BiomesEditorDialog(self)
        self.dialog_biomes.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_factions = FactionsEditorDialog(self)
        self.dialog_factions.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_provinces = ParagonsEditorDialog(self)
        self.dialog_provinces.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_religions = ChaosPathsEditorDialog(self)
        self.dialog_religions.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_cultures = FringeGroupsEditorDialog(self)
        self.dialog_cultures.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_chaos = ChaosEditorDialog(self)
        self.dialog_chaos.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_settlements = SettlementsEditorDialog(self)
        self.dialog_settlements.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_names = NameStyleEditorDialog(self)
        self.dialog_names.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_markers = MarkersEditorDialog(self)
        self.dialog_markers.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_forces = ForcesEditorDialog(self)
        self.dialog_forces.setWindowFlags(Qt.WindowType.Widget)
        
        self.dialog_routes = RoutesEditorDialog(self)
        self.dialog_routes.setWindowFlags(Qt.WindowType.Widget)
        
        for dlg in [
            self.dialog_elevation, self.dialog_biomes, self.dialog_factions,
            self.dialog_provinces, self.dialog_religions, self.dialog_cultures,
            self.dialog_chaos, self.dialog_settlements, self.dialog_names,
            self.dialog_markers, self.dialog_forces, self.dialog_routes
        ]:
            dlg.setStyleSheet("""
                QDialog {
                    background-color: #111216;
                    border: none;
                }
                QWidget {
                    background-color: #111216;
                }
            """)
        
        # --- PAGE 0: CHECKLIST ---
        page_checklist = QWidget()
        lay_check = QVBoxLayout(page_checklist)
        
        lay_check.addWidget(QLabel("<b>HISTORICAL TIMELINE SLIDER (Temporal Engine)</b>"))
        timeline_lay = QHBoxLayout()
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.slider_timeline.setRange(0, 3000)
        self.slider_timeline.setValue(2000)
        self.slider_timeline.valueChanged.connect(self.on_timeline_changed)
        self.lbl_timeline_year = QLabel("Year: 2000")
        timeline_lay.addWidget(self.slider_timeline)
        timeline_lay.addWidget(self.lbl_timeline_year)
        lay_check.addLayout(timeline_lay)
        
        lay_check.addWidget(QLabel("<b>ACTIVE Z-DIMENSION SLICE</b>"))
        self.cb_z_layer = QComboBox()
        self.cb_z_layer.addItems(["Surface", "Sky Layer 1", "Sky Layer 2", "Subterranean U1", "Subterranean U2", "Leylines / Magic Layer"])
        self.cb_z_layer.currentIndexChanged.connect(self.on_z_layer_changed)
        lay_check.addWidget(self.cb_z_layer)
        
        lay_check.addWidget(QLabel("<b>COSMOVISION PERSPECTIVE (Narrator Profile)</b>"))
        self.cb_narrator = QComboBox()
        self.cb_narrator.addItem("Objective Reality", None)
        for n in self.worldsmith_config.get("unreliable_narrators", []):
            self.cb_narrator.addItem(n["display_name"], n["profile_id"])
        self.cb_narrator.currentIndexChanged.connect(self.on_narrator_changed)
        lay_check.addWidget(self.cb_narrator)
        
        self.gp_ai_scope = QGroupBox("AI Auditor Configuration Matrix")
        ai_scope_lay = QVBoxLayout(self.gp_ai_scope)
        self.chk_timeline = QCheckBox("Audit Chronological Timeline Gaps")
        self.chk_factions = QCheckBox("Audit Faction Currency Consistency")
        self.chk_climate = QCheckBox("Audit Climate / Wind Physics")
        self.chk_hydrology = QCheckBox("Audit Hydrology / River Gravity")
        self.chk_timeline.setChecked(True)
        self.chk_factions.setChecked(True)
        self.chk_timeline.stateChanged.connect(self.save_ai_scope_settings)
        self.chk_factions.stateChanged.connect(self.save_ai_scope_settings)
        self.chk_climate.stateChanged.connect(self.save_ai_scope_settings)
        self.chk_hydrology.stateChanged.connect(self.save_ai_scope_settings)
        ai_scope_lay.addWidget(self.chk_timeline)
        ai_scope_lay.addWidget(self.chk_factions)
        ai_scope_lay.addWidget(self.chk_climate)
        ai_scope_lay.addWidget(self.chk_hydrology)
        lay_check.addWidget(self.gp_ai_scope)
        
        lay_check.addWidget(QLabel("<b>WORLD COMPLETENESS</b>"))
        self.progress_bar = QProgressBar()
        lay_check.addWidget(self.progress_bar)
        
        lay_check.addWidget(QLabel("<b>Lore Gaps & System Conflicts:</b>"))
        self.gaps_table = QTableWidget()
        self.gaps_table.setColumnCount(3)
        self.gaps_table.setHorizontalHeaderLabels(["Subject", "Type", "Issue Description"])
        self.gaps_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.gaps_table.itemSelectionChanged.connect(self.on_gap_selected)
        lay_check.addWidget(self.gaps_table)
        
        self.group_resolve = QGroupBox("Resolve Selected Issue")
        resolve_lay = QVBoxLayout(self.group_resolve)
        self.lbl_resolve_question = QLabel("Select an issue above to clarify.")
        self.lbl_resolve_question.setWordWrap(True)
        resolve_lay.addWidget(self.lbl_resolve_question)
        self.text_resolve_answer = QTextEdit()
        self.text_resolve_answer.setPlaceholderText("Type your lore clarification here...")
        self.text_resolve_answer.setMaximumHeight(80)
        resolve_lay.addWidget(self.text_resolve_answer)
        self.btn_submit_clarification = QPushButton("Submit Clarification")
        self.btn_submit_clarification.clicked.connect(self.submit_clarification)
        self.btn_submit_clarification.setEnabled(False)
        self.btn_ai_draft = QPushButton("Draft Resolution (AI)")
        self.btn_ai_draft.clicked.connect(self.ask_ai_to_draft_resolution)
        self.btn_ai_draft.setEnabled(False)
        resolve_lay.addWidget(self.btn_submit_clarification)
        resolve_lay.addWidget(self.btn_ai_draft)
        lay_check.addWidget(self.group_resolve)
        
        # --- PAGE 13: LORE NOTES EDITOR ---
        page_lore = QWidget()
        lay_lore = QHBoxLayout(page_lore)
        
        tree_pane = QWidget()
        lay_tree = QVBoxLayout(tree_pane)
        lay_tree.addWidget(QLabel("<b>Lore Vault Notes</b>"))
        self.tree_notes = QTreeWidget()
        self.tree_notes.setHeaderHidden(True)
        self.tree_notes.itemClicked.connect(self.load_selected_note)
        lay_tree.addWidget(self.tree_notes)
        self.btn_new_note = QPushButton("New Vault Note")
        self.btn_new_note.clicked.connect(self.create_new_note)
        lay_tree.addWidget(self.btn_new_note)
        lay_lore.addWidget(tree_pane, 1)
        
        edit_pane = QWidget()
        lay_edit = QVBoxLayout(edit_pane)
        self.lbl_editing_file = QLabel("No note selected.")
        lay_edit.addWidget(self.lbl_editing_file)
        self.lbl_attached_image = QLabel("No illustrations linked.")
        self.lbl_attached_image.setStyleSheet("color: #6366F1; font-weight: bold;")
        lay_edit.addWidget(self.lbl_attached_image)
        self.editor = QTextEdit()
        lay_edit.addWidget(self.editor)
        
        edit_ctrls = QHBoxLayout()
        self.btn_save_note = QPushButton("Save Note")
        self.btn_save_note.clicked.connect(self.save_current_note)
        self.btn_save_note.setEnabled(False)
        self.btn_auto_tag = QPushButton("Auto-Categorize")
        self.btn_auto_tag.clicked.connect(self.auto_categorize_note)
        self.btn_auto_tag.setEnabled(False)
        edit_ctrls.addWidget(self.btn_save_note)
        edit_ctrls.addWidget(self.btn_auto_tag)
        lay_edit.addLayout(edit_ctrls)
        
        self.gp_scaffold = QGroupBox("Insert Template Scaffold")
        scaff_lay = QHBoxLayout(self.gp_scaffold)
        self.cb_scaffolds = QComboBox()
        self.cb_scaffolds.addItems(["Character Sheet", "Location Sheet", "Faction Sheet", "Historical Event"])
        self.btn_insert_scaffold = QPushButton("Inject")
        self.btn_insert_scaffold.clicked.connect(self.inject_scaffold_template)
        scaff_lay.addWidget(self.cb_scaffolds)
        scaff_lay.addWidget(self.btn_insert_scaffold)
        lay_edit.addWidget(self.gp_scaffold)
        
        self.gp_ai_inquiry = QGroupBox("AI World Inquiry Board")
        inq_lay = QVBoxLayout(self.gp_ai_inquiry)
        self.lbl_ai_inquiry = QLabel("Select a note to scan for narrative gaps and auto-inquire details.")
        self.lbl_ai_inquiry.setWordWrap(True)
        self.lbl_ai_inquiry.setStyleSheet("color: #E2E8F0; font-size: 11px;")
        inq_lay.addWidget(self.lbl_ai_inquiry)
        lay_edit.addWidget(self.gp_ai_inquiry)
        lay_lore.addWidget(edit_pane, 2)
        
        # --- PAGE 14: CHRONICLE TIMELINE ---
        page_timeline = QWidget()
        lay_time = QVBoxLayout(page_timeline)
        
        header_lay = QHBoxLayout()
        header_lay.addWidget(QLabel("<b>Historical Chronicle Events</b>"))
        self.cb_timeline_filter = QComboBox()
        self.cb_timeline_filter.addItems(["All Items", "Pins Only", "Frames Only"])
        self.cb_timeline_filter.currentIndexChanged.connect(self.refresh_events_list)
        header_lay.addWidget(QLabel("Filter:"))
        header_lay.addWidget(self.cb_timeline_filter)
        lay_time.addLayout(header_lay)
        
        self.table_events = QTableWidget()
        self.table_events.setColumnCount(5)
        self.table_events.setHorizontalHeaderLabels(["Start Year", "End Year", "Event Name", "Location Q,R", "Description"])
        self.table_events.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_events.itemSelectionChanged.connect(self.on_event_row_selected)
        lay_time.addWidget(self.table_events)
        
        self.form_box = QGroupBox("Add / Edit Chronology Event (Pins & Frames)")
        form_lay = QFormLayout(self.form_box)
        self.txt_ev_year = QSpinBox()
        self.txt_ev_year.setRange(0, 3000)
        self.txt_ev_year.setValue(2000)
        
        self.cb_ev_type = QComboBox()
        self.cb_ev_type.addItems(["Point Event (Pin)", "Duration Frame"])
        self.cb_ev_type.currentIndexChanged.connect(self.on_ev_type_changed)
        
        self.txt_ev_end_year = QSpinBox()
        self.txt_ev_end_year.setRange(0, 3000)
        self.txt_ev_end_year.setValue(2000)
        self.txt_ev_end_year.setEnabled(False)
        
        self.txt_ev_name = QLineEdit()
        self.txt_ev_q = QSpinBox()
        self.txt_ev_q.setRange(-150, 150)
        self.txt_ev_r = QSpinBox()
        self.txt_ev_r.setRange(-150, 150)
        self.txt_ev_desc = QTextEdit()
        self.txt_ev_desc.setMaximumHeight(60)
        
        self.cb_ev_link = QComboBox()
        self.cb_ev_link.addItem("None")
        
        form_lay.addRow("Event Type:", self.cb_ev_type)
        form_lay.addRow("Start Year:", self.txt_ev_year)
        form_lay.addRow("End Year (Frame):", self.txt_ev_end_year)
        form_lay.addRow("Event Name:", self.txt_ev_name)
        form_lay.addRow("Q Coord:", self.txt_ev_q)
        form_lay.addRow("R Coord:", self.txt_ev_r)
        form_lay.addRow("Link Lore Note:", self.cb_ev_link)
        form_lay.addRow("Description:", self.txt_ev_desc)
        
        btn_lay = QHBoxLayout()
        self.btn_add_event = QPushButton("Save Event")
        self.btn_add_event.clicked.connect(self.save_event_to_chronicle)
        self.btn_delete_event = QPushButton("Delete Selected")
        self.btn_delete_event.clicked.connect(self.delete_selected_event)
        self.btn_delete_event.setStyleSheet("background-color: #E74C3C;")
        btn_lay.addWidget(self.btn_add_event)
        btn_lay.addWidget(self.btn_delete_event)
        form_lay.addRow(btn_lay)
        lay_time.addWidget(self.form_box)
        
        # --- PAGE 15: MOONS & CALENDAR MATRIX ---
        page_calendar = QWidget()
        lay_cal = QVBoxLayout(page_calendar)
        
        lay_cal.addWidget(QLabel("<b>CUSTOM SOLAR CALENDAR MATRIX</b>"))
        self.txt_calendar_config = QTextEdit()
        self.txt_calendar_config.setMaximumHeight(80)
        self.txt_calendar_config.setPlainText(json.dumps(self.worldsmith_config.get("calendar_settings", {}), indent=2))
        self.btn_save_calendar = QPushButton("Save Solar Calendar Config")
        self.btn_save_calendar.clicked.connect(self.save_calendar_settings)
        lay_cal.addWidget(self.txt_calendar_config)
        lay_cal.addWidget(self.btn_save_calendar)
        
        lay_cal.addWidget(QLabel("<b>LUNAR MOONS MATRIX CONFIGURATOR</b>"))
        self.table_moons = QTableWidget()
        self.table_moons.setColumnCount(3)
        self.table_moons.setHorizontalHeaderLabels(["Moon Name", "Orbital Period (Days)", "Luminescence Hex"])
        self.table_moons.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay_cal.addWidget(self.table_moons)
        
        moon_btn_lay = QHBoxLayout()
        btn_add_moon = QPushButton("Add Moon Row")
        btn_add_moon.clicked.connect(self.on_add_moon_row)
        btn_del_moon = QPushButton("Remove Selected Moon")
        btn_del_moon.clicked.connect(self.on_del_moon_row)
        btn_save_moons = QPushButton("Save Moons Config")
        btn_save_moons.clicked.connect(self.save_moons_settings)
        moon_btn_lay.addWidget(btn_add_moon)
        moon_btn_lay.addWidget(btn_del_moon)
        moon_btn_lay.addWidget(btn_save_moons)
        lay_cal.addLayout(moon_btn_lay)
        
        self.lbl_lunar_status = QLabel("Moons Loading...")
        lay_cal.addWidget(self.lbl_lunar_status)
        
        lay_cal.addWidget(QLabel("<b>ASTRONOMICAL SKY DOME ORBITS PREVIEW</b>"))
        self.celestial_preview = CelestialPreviewWidget(self)
        lay_cal.addWidget(self.celestial_preview)
        
        # --- PAGE 16: AI MAP ASSISTANT ---
        page_assist = QWidget()
        lay_assist = QVBoxLayout(page_assist)
        
        lay_assist.addWidget(QLabel("<b>AI-Assisted Cartographer Placement Board</b>"))
        self.txt_ai_advice = QTextEdit()
        self.txt_ai_advice.setReadOnly(True)
        self.txt_ai_advice.setPlaceholderText("Select one of the assistant options below to suggest map placements, organize timelines, or calculate stable calendars...")
        lay_assist.addWidget(self.txt_ai_advice)
        
        self.btn_suggest_map = QPushButton("Suggest Optimal Settlement Centroids")
        self.btn_suggest_map.clicked.connect(self.suggest_map_placements)
        self.btn_suggest_chron = QPushButton("Extract Timeline from Vault Notes")
        self.btn_suggest_chron.clicked.connect(self.suggest_timeline)
        self.btn_suggest_cosmo = QPushButton("Design Balanced Solar System Orbits")
        self.btn_suggest_cosmo.clicked.connect(self.suggest_cosmology)
        
        lay_assist.addWidget(self.btn_suggest_map)
        lay_assist.addWidget(self.btn_suggest_chron)
        lay_assist.addWidget(self.btn_suggest_cosmo)
        
        self.btn_apply_placements = QPushButton("Apply Placements & Borders to Database")
        self.btn_apply_placements.setEnabled(False)
        self.btn_apply_placements.clicked.connect(self.apply_suggested_placements)
        self.btn_apply_timeline = QPushButton("Apply Events to Chronicle History")
        self.btn_apply_timeline.setEnabled(False)
        self.btn_apply_timeline.clicked.connect(self.apply_suggested_timeline)
        
        lay_assist.addWidget(self.btn_apply_placements)
        lay_assist.addWidget(self.btn_apply_timeline)
        lay_assist.addStretch()
        
        # --- PAGE 5: CITY LAYOUT VIEWER (Embedded at Index 17) ---
        page_city = QWidget()
        lay_city = QVBoxLayout(page_city)
        self.lbl_city_title = QLabel("<b>No Settlement Selected</b>")
        self.lbl_city_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_city.addWidget(self.lbl_city_title)
        
        self.lbl_city_image = QLabel("Select a settlement on the map to view its city layout.")
        self.lbl_city_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_city_image.setWordWrap(True)
        self.lbl_city_image.setStyleSheet("border: 1px dashed #29292E; background-color: #0b0c10; padding: 20px;")
        lay_city.addWidget(self.lbl_city_image)
        
        self.btn_regen_city = QPushButton("Regenerate City Layout")
        self.btn_regen_city.clicked.connect(self.regenerate_current_city)
        self.btn_regen_city.setEnabled(False)
        lay_city.addWidget(self.btn_regen_city)
        lay_city.addStretch()
        
        # --- PAGE 6: ILLUSTRATIONS INGEST (Embedded at Index 18) ---
        page_img = QWidget()
        lay_img = QVBoxLayout(page_img)
        group_image = QGroupBox("Import Illustrations")
        img_form = QFormLayout(group_image)
        self.txt_img_path = QLineEdit()
        self.btn_browse_img = QPushButton("Browse...")
        self.btn_browse_img.clicked.connect(self.browse_image)
        img_file_lay = QHBoxLayout()
        img_file_lay.addWidget(self.txt_img_path)
        img_file_lay.addWidget(self.btn_browse_img)
        img_form.addRow("Image File:", img_file_lay)
        
        self.txt_img_desc = QLineEdit()
        self.txt_img_desc.setPlaceholderText("e.g. Portrait of Fox-kin Elder")
        img_form.addRow("Description:", self.txt_img_desc)
        
        self.cb_img_subject = QComboBox()
        img_form.addRow("Subject Link:", self.cb_img_subject)
        
        self.btn_ingest_image = QPushButton("Ingest & Link Image")
        self.btn_ingest_image.clicked.connect(self.ingest_image)
        img_form.addRow(self.btn_ingest_image)
        lay_img.addWidget(group_image)
        lay_img.addStretch()
        
        # --- PAGE 7: TEMPLATES & LAYERS CONFIG (Embedded at Index 19) ---
        page_temp = QWidget()
        lay_temp = QVBoxLayout(page_temp)
        
        self.gp_custom_layer = QGroupBox("Custom Layer Registration Factory")
        lay_lay = QFormLayout(self.gp_custom_layer)
        self.txt_layer_name = QLineEdit()
        self.txt_layer_name.setPlaceholderText("e.g. Astral Plane")
        lay_lay.addRow("Layer Name:", self.txt_layer_name)
        self.btn_create_layer = QPushButton("Create Dynamic Layer")
        self.btn_create_layer.clicked.connect(self.register_custom_layer)
        lay_lay.addRow(self.btn_create_layer)
        lay_temp.addWidget(self.gp_custom_layer)
        
        self.gp_custom_field = QGroupBox("Template Custom EAV Fields Builder")
        fld_lay = QFormLayout(self.gp_custom_field)
        self.cb_target_template = QComboBox()
        self.cb_target_template.addItems(["character", "faction", "location", "event", "superpower"])
        fld_lay.addRow("Target Template:", self.cb_target_template)
        self.txt_field_name = QLineEdit()
        self.txt_field_name.setPlaceholderText("e.g. power_class")
        fld_lay.addRow("Field Name:", self.txt_field_name)
        self.cb_field_type = QComboBox()
        self.cb_field_type.addItems(["string", "number", "boolean", "document_link"])
        fld_lay.addRow("Field Type:", self.cb_field_type)
        self.chk_field_required = QCheckBox("Field Required")
        fld_lay.addRow(self.chk_field_required)
        self.btn_create_field = QPushButton("Inject Field Definition")
        self.btn_create_field.clicked.connect(self.inject_custom_field)
        fld_lay.addRow(self.btn_create_field)
        lay_temp.addWidget(self.gp_custom_field)
        
        self.gp_wind_bands = QGroupBox("Prevailing Wind Bands Configurator")
        wind_lay = QFormLayout(self.gp_wind_bands)
        self.txt_wind_bands = QTextEdit()
        self.txt_wind_bands.setPlainText(json.dumps(self.worldsmith_config.get("wind_bands", []), indent=2))
        self.txt_wind_bands.setMaximumHeight(80)
        self.btn_save_wind_bands = QPushButton("Save Wind Bands Configuration")
        self.btn_save_wind_bands.clicked.connect(self.save_wind_bands_config)
        wind_lay.addRow("Wind Bands JSON:", self.txt_wind_bands)
        wind_lay.addRow(self.btn_save_wind_bands)
        lay_temp.addWidget(self.gp_wind_bands)
        
        self.gp_narrators_config = QGroupBox("Cosmovision Narrators Configurator")
        narr_lay = QFormLayout(self.gp_narrators_config)
        self.txt_narrators_config = QTextEdit()
        self.txt_narrators_config.setMaximumHeight(80)
        self.txt_narrators_config.setPlainText(json.dumps(self.worldsmith_config.get("unreliable_narrators", []), indent=2))
        self.btn_save_narrators = QPushButton("Save Narrators List")
        self.btn_save_narrators.clicked.connect(self.save_narrators_settings)
        narr_lay.addRow("Narrators List JSON:", self.txt_narrators_config)
        narr_lay.addRow(self.btn_save_narrators)
        lay_temp.addWidget(self.gp_narrators_config)
        lay_temp.addStretch()
        
        # --- PAGE 8: DISEASE & MAGIC BRUSHES (Embedded at Index 20) ---
        page_dm = QWidget()
        lay_dm = QVBoxLayout(page_dm)
        
        lay_dm.addWidget(QLabel("<b>EPIDEMIOLOGY TRANS-VECTOR OUTBREAK SIMULATOR</b>"))
        self.btn_paint_disease = QPushButton("Paint Patient Zero (Outbreak)")
        self.btn_paint_disease.clicked.connect(self.paint_outbreak_tool)
        lay_dm.addWidget(self.btn_paint_disease)
        self.cb_transmission = QComboBox()
        self.cb_transmission.addItems(["Airborne (Wind-Bound)", "Commercial (Trade-Bound)", "Vermin-Vector (Terrain-Bound)", "Magical Vector (Leyline-Bound)"])
        lay_dm.addWidget(self.cb_transmission)
        self.btn_step_disease = QPushButton("Simulate Outbreak Expansion Step")
        self.btn_step_disease.clicked.connect(self.run_disease_step)
        lay_dm.addWidget(self.btn_step_disease)
        self.lbl_disease_status = QLabel("Paint outbreak centers, choose transmission vector, and simulate outbreak expansion.")
        self.lbl_disease_status.setWordWrap(True)
        lay_dm.addWidget(self.lbl_disease_status)
        
        lay_dm.addWidget(QLabel("<b>🔮 ARCANE LEYLINES & ANOMALY BRUSHBOARD</b>"))
        self.btn_paint_magic = QPushButton("Paint Magical Anomaly Zone")
        self.btn_paint_magic.clicked.connect(self.paint_magic_anomaly_tool)
        lay_dm.addWidget(self.btn_paint_magic)
        self.btn_draw_leyline = QPushButton("Paint High Magic Node (Leyline Anchor)")
        self.btn_draw_leyline.clicked.connect(self.paint_leyline_anchor_tool)
        lay_dm.addWidget(self.btn_draw_leyline)
        self.lbl_magic_warnings = QLabel("Select arcane tools to paint power networks directly onto coordinates.")
        self.lbl_magic_warnings.setWordWrap(True)
        lay_dm.addWidget(self.lbl_magic_warnings)
        
        lay_dm.addWidget(QLabel("<b>ASTRONOMICAL CELESTIAL HORIZON SPHERE</b>"))
        self.lbl_visible_constellations = QLabel("Select a coordinate to check constellation horizon visibility.")
        self.lbl_visible_constellations.setWordWrap(True)
        lay_dm.addWidget(self.lbl_visible_constellations)
        lay_dm.addStretch()
        
        # --- PAGE 9: DATA PORTAL (Embedded at Index 21) ---
        page_export = QWidget()
        lay_exp = QVBoxLayout(page_export)
        
        self.btn_verify = QPushButton("Verify World Completeness Gaps")
        self.btn_verify.clicked.connect(self.run_verification)
        lay_exp.addWidget(self.btn_verify)
        
        self.btn_forge_vault = QPushButton("Compile definitive Obsidian Vault Book")
        self.btn_forge_vault.clicked.connect(self.run_vault_forge)
        lay_exp.addWidget(self.btn_forge_vault)
        
        self.btn_export_web_wiki = QPushButton("Compile Web Wiki slides manifest")
        self.btn_export_web_wiki.clicked.connect(self.export_web_wiki)
        lay_exp.addWidget(self.btn_export_web_wiki)
        
        lay_exp.addWidget(QLabel("<b>Reverse Cartography Batch Seed:</b>"))
        self.btn_reverse_cart = QPushButton("Import unstructured Notes Folder")
        self.btn_reverse_cart.clicked.connect(self.run_reverse_cartography)
        lay_exp.addWidget(self.btn_reverse_cart)
        
        lay_exp.addWidget(QLabel("<b>Export Formats:</b>"))
        self.btn_export_world_json = QPushButton("Export World State JSON")
        self.btn_export_world_json.clicked.connect(self.export_worldbuilder_json)
        lay_exp.addWidget(self.btn_export_world_json)
        
        self.btn_export_geojson = QPushButton("Export Boundaries GeoJSON")
        self.btn_export_geojson.clicked.connect(self.export_geojson)
        lay_exp.addWidget(self.btn_export_geojson)
        lay_exp.addStretch()

        # Add all pages to stacked widget in order of sidebar items
        self.stacked_widget.addWidget(page_checklist)            # Index 0
        self.stacked_widget.addWidget(self.dialog_elevation)      # Index 1
        self.stacked_widget.addWidget(self.dialog_biomes)         # Index 2
        self.stacked_widget.addWidget(self.dialog_factions)       # Index 3
        self.stacked_widget.addWidget(self.dialog_provinces)      # Index 4
        self.stacked_widget.addWidget(self.dialog_religions)      # Index 5
        self.stacked_widget.addWidget(self.dialog_cultures)       # Index 6
        self.stacked_widget.addWidget(self.dialog_chaos)          # Index 7
        self.stacked_widget.addWidget(self.dialog_settlements)    # Index 8
        self.stacked_widget.addWidget(self.dialog_names)          # Index 9
        self.stacked_widget.addWidget(self.dialog_markers)        # Index 10
        self.stacked_widget.addWidget(self.dialog_forces)         # Index 11
        self.stacked_widget.addWidget(self.dialog_routes)         # Index 12
        self.stacked_widget.addWidget(page_lore)                  # Index 13
        self.stacked_widget.addWidget(page_timeline)              # Index 14
        self.stacked_widget.addWidget(page_calendar)              # Index 15
        self.stacked_widget.addWidget(page_assist)                # Index 16
        self.stacked_widget.addWidget(page_city)                  # Index 17
        self.stacked_widget.addWidget(page_img)                   # Index 18
        self.stacked_widget.addWidget(page_temp)                  # Index 19
        self.stacked_widget.addWidget(page_dm)                    # Index 20
        self.stacked_widget.addWidget(page_export)                # Index 21

        # Re-purpose left dock to contain the master sidebar list
        if hasattr(self, "left_dock"):
            left_container = QWidget()
            left_lay = QVBoxLayout(left_container)
            left_lay.setContentsMargins(0, 0, 0, 0)
            
            self.left_sidebar_list = QListWidget()
            self.left_sidebar_list.setStyleSheet("""
                QListWidget {
                    background-color: #0E0F14;
                    border: none;
                    color: #A0A5B5;
                    font-weight: 500;
                }
                QListWidget::item {
                    height: 36px;
                    padding-left: 8px;
                    border-left: 3px solid transparent;
                }
                QListWidget::item:hover {
                    background-color: #16171E;
                    color: #F1F5F9;
                }
                QListWidget::item:selected {
                    background-color: #1E202B;
                    color: #6366F1;
                    border-left: 3px solid #6366F1;
                    font-weight: bold;
                }
            """)
            
            self.left_sidebar_list.addItems([
                "Checklist & Audit",
                "Elevation and Peaks",
                "Biomes Editor",
                "Factions & States",
                "Legends and Heroes",
                "Religions and Faiths",
                "Cultures and Species",
                "Arcane Anomalies",
                "Settlements Directory",
                "Language & Names",
                "Markers and POIs",
                "Faction Garrisons",
                "Trade Routes Editor",
                "Lore Vault Notes",
                "Chronicle Timeline",
                "Moons & Calendar",
                "AI Map Assistant",
                "City Layout Viewer",
                "Illustrations Ingest",
                "Custom Templates",
                "Epidemiology Simulator",
                "Data Portal Exporters"
            ])
            self.left_sidebar_list.currentRowChanged.connect(self.on_left_sidebar_changed)
            left_lay.addWidget(self.left_sidebar_list)
            self.left_dock.setWidget(left_container)

        # Add a button to the toolbar to open the Lore Book & AI Writer companion
        for tb in self.findChildren(QToolBar):
            btn_companion = QPushButton("📖 Lore Book Companion")
            btn_companion.setStyleSheet("background-color: #8B5CF6; color: white; font-weight: bold;")
            btn_companion.clicked.connect(self.open_lore_book_companion)
            tb.addWidget(btn_companion)
            break

        self.setWindowTitle("Ostraka Worldsmith Sandbox & Map Editor")
        
        # Override the simulator "Run Tick" toolbar button to act as "Advance Year"
        for tb in self.findChildren(QToolBar):
            for btn in tb.findChildren(QPushButton):
                if "Run Tick" in btn.text() or "Run" in btn.text() or "Tick" in btn.text():
                    btn.setText("Advance Year")
                    btn.setToolTip("Advance chronological timeline by 1 year")
        
        self.refresh_notes_list()
        self.refresh_events_list()
        self.populate_moons_table()
        self.check_lunar_conjunctions()
        self.celestial_preview.update()

    def open_lore_book_companion(self):
        if not hasattr(self, "lore_book_dialog") or self.lore_book_dialog is None:
            self.lore_book_dialog = LoreBookAIWriterWindow(self)
        self.lore_book_dialog.show()
        self.lore_book_dialog.raise_()
        self.lore_book_dialog.activateWindow()

    def update_inspect_display(self, q, r):
        if not hasattr(self, "state") or not self.state:
            return
        hx = self.state.hexes.get((q, r))
        if not hx:
            return
            
        self.lbl_inspect_coords.setText(f"<b>Coords:</b> q={q}, r={r}")
        
        # Elevation & Biome
        elev_m = hx.elevation * 100
        biome_names = {
            0: "Jungle", 1: "Forest", 2: "Taiga", 3: "Desert", 
            4: "Plains", 5: "Tundra", 6: "Mountain", 7: "Volcano", 
            8: "Arctic", 9: "Ocean", 10: "Coral Reef", 11: "Arctic Ocean",
            12: "Abyssal Trench", 13: "Prison Wastes"
        }
        biome_str = biome_names.get(hx.biome, f"Unknown ({hx.biome})")
        self.lbl_inspect_terrain.setText(f"<b>Terrain:</b> Elev: {elev_m}m | Biome: {biome_str}")
        
        # Settlement
        if hx.settlement:
            faction_name = "Independent"
            if hx.settlement.faction_id in self.state.factions:
                faction_name = self.state.factions[hx.settlement.faction_id].name
            self.lbl_inspect_settlement.setText(f"<b>Settlement:</b> {hx.settlement.name} (Pop: {hx.settlement.population}) | Faction: {faction_name}")
        else:
            self.lbl_inspect_settlement.setText("<b>Settlement:</b> None")
            
        # Magic & Anomaly
        magic_res = getattr(hx, "res", 0)
        anomaly = getattr(hx, "chaos_domain", "None") or "None"
        self.lbl_inspect_magic.setText(f"<b>Magic:</b> Level {magic_res} | <b>Anomaly:</b> {anomaly}")
        
        # Garrison
        garrisons = []
        for g in self.state.forces.values():
            if getattr(g, "global_hex_id", None) == hx.id:
                garrisons.append(f"{g.name} ({g.type})")
        garrison_str = ", ".join(garrisons) if garrisons else "None"
        self.lbl_inspect_garrison.setText(f"<b>Garrison:</b> {garrison_str}")

    def on_left_sidebar_changed(self, idx):
        if idx >= 0:
            self.stacked_widget.setCurrentIndex(idx)

    # --- QTreeWidget Notes Folder Operations ---
    def refresh_notes_list(self):
        import lore_forge
        self.tree_notes.clear()
        self.cb_ev_link.clear()
        self.cb_ev_link.addItem("None")
        
        if not os.path.exists(lore_forge.LORE_DB):
            return
            
        cats = sorted([c for c in os.listdir(lore_forge.LORE_DB) if os.path.isdir(os.path.join(lore_forge.LORE_DB, c))])
        for cat in cats:
            cat_item = QTreeWidgetItem(self.tree_notes, [cat])
            cat_path = os.path.join(lore_forge.LORE_DB, cat)
            subjects = sorted([s for s in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, s))])
            for subj in subjects:
                subj_path = os.path.join(cat_path, subj)
                files = [f for f in os.listdir(subj_path) if f.endswith(".md")]
                for f in files:
                    note_item = QTreeWidgetItem(cat_item, [f.replace(".md", "")])
                    note_item.setData(0, Qt.ItemDataRole.UserRole, os.path.join(subj_path, f))
                    self.cb_ev_link.addItem(f.replace(".md", ""))

    def load_selected_note(self):
        import lore_forge
        item = self.tree_notes.currentItem()
        if not item:
            return
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not file_path or not os.path.exists(file_path):
            return
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.editor.setPlainText(content)
        self.lbl_editing_file.setText(f"Editing: {os.path.basename(file_path)}")
        self.btn_save_note.setEnabled(True)
        self.btn_auto_tag.setEnabled(True)
        self.current_note_path = file_path
        
        # Attached illustration preview
        subject_name = os.path.basename(file_path).replace(".md", "")
        img_suggest = lore_forge.find_image_for_subject(subject_name)
        if img_suggest:
            self.lbl_attached_image.setText(f"Attached Visual Clue: {img_suggest}")
        else:
            self.lbl_attached_image.setText("No visual illustrations linked.")
            
        # AI Gaps Inquiry suggests
        self.lbl_ai_inquiry.setText("AI is scanning this note to draft worldbuilding inquiries...")
        self.start_ai_task("ai_suggest_inquiries", {"text": content, "title": subject_name})

    def save_current_note(self):
        if not self.current_note_path:
            return
        content = self.editor.toPlainText()
        try:
            with open(self.current_note_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Success", "Vault note saved successfully!")
            self.refresh_notes_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save note: {e}")

    def auto_categorize_note(self):
        if not self.current_note_path:
            return
        content = self.editor.toPlainText()
        self.btn_auto_tag.setEnabled(False)
        self.start_ai_task("ai_classify_note", {"text": content})

    def create_new_note(self):
        import lore_forge
        name, ok = QLineEdit.getText(self, "New Vault Note", "Enter subject name for new vault note:")
        if ok and name.strip():
            safe_name = name.strip()
            # Default to unclassified
            subj_dir = os.path.join(lore_forge.LORE_DB, "unclassified", safe_name)
            os.makedirs(subj_dir, exist_ok=True)
            file_path = os.path.join(subj_dir, f"{safe_name}.md")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {safe_name}\n\nType your notes here...")
                
            self.refresh_notes_list()
            self.editor.setPlainText(f"# {safe_name}\n\nType your notes here...")
            self.lbl_editing_file.setText(f"Editing: {safe_name}.md")
            self.btn_save_note.setEnabled(True)
            self.btn_auto_tag.setEnabled(True)
            self.current_note_path = file_path

    def inject_scaffold_template(self):
        sc = self.cb_scaffolds.currentText()
        scaffolds = {
            "Character Sheet": "## Character Information\n- **Species/Faction**: \n- **Role**: \n- **Key Motivation**: \n\n## History\n- Birth year: \n- Notable events: ",
            "Location Sheet": "## Location Information\n- **Terrain/Biome**: \n- **Faction Control**: \n- **Resources**: \n\n## Points of Interest\n1. \n2. ",
            "Faction Sheet": "## Faction Matrix\n- **Governance**: \n- **Territorial bounds**: \n- **Borders & Relations**: \n\n## Economy\n- Primary goods: ",
            "Historical Event": "## Historic Chronicle\n- **Year occurred**: \n- **Key entities**: \n- **Description**: "
        }
        self.editor.insertPlainText(scaffolds.get(sc, ""))

    # --- Timeline Events Chronicle Operations ---
    def on_ev_type_changed(self):
        is_frame = self.cb_ev_type.currentText() == "Duration Frame"
        self.txt_ev_end_year.setEnabled(is_frame)

    def refresh_events_list(self):
        self.table_events.setRowCount(0)
        if not os.path.exists(self.db_path):
            return
            
        filt = self.cb_timeline_filter.currentText()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if filt == "Pins Only":
                cursor.execute("SELECT year, end_year, name, global_q, global_r, description FROM chronology_events WHERE end_year IS NULL OR end_year = year ORDER BY year ASC")
            elif filt == "Frames Only":
                cursor.execute("SELECT year, end_year, name, global_q, global_r, description FROM chronology_events WHERE end_year IS NOT NULL AND end_year > year ORDER BY year ASC")
            else:
                cursor.execute("SELECT year, end_year, name, global_q, global_r, description FROM chronology_events ORDER BY year ASC")
                
            rows = cursor.fetchall()
            for r_idx, r in enumerate(rows):
                self.table_events.insertRow(r_idx)
                self.table_events.setItem(r_idx, 0, QTableWidgetItem(str(r[0])))
                self.table_events.setItem(r_idx, 1, QTableWidgetItem(str(r[1] or "")))
                self.table_events.setItem(r_idx, 2, QTableWidgetItem(str(r[2])))
                self.table_events.setItem(r_idx, 3, QTableWidgetItem(f"{r[3]},{r[4]}"))
                self.table_events.setItem(r_idx, 4, QTableWidgetItem(str(r[5] or "")))
            conn.close()
        except Exception as e:
            print(f"[-] Timeline refresh failed: {e}")

    def save_event_to_chronicle(self):
        year = self.txt_ev_year.value()
        is_frame = self.cb_ev_type.currentText() == "Duration Frame"
        end_year = self.txt_ev_end_year.value() if is_frame else year
        name = self.txt_ev_name.text().strip()
        desc = self.txt_ev_desc.toPlainText().strip()
        q = self.txt_ev_q.value()
        r = self.txt_ev_r.value()
        linked_note = self.cb_ev_link.currentText()
        
        associated = [linked_note] if linked_note and linked_note != "None" else []
        associated_json = json.dumps(associated)
        
        if not name:
            QMessageBox.warning(self, "Empty Name", "Please enter an event name.")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM chronology_events WHERE name = ? AND year = ?", (name, year))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("""
                    UPDATE chronology_events 
                    SET end_year = ?, description = ?, global_q = ?, global_r = ?, associated_entities_json = ?
                    WHERE id = ?
                """, (end_year, desc, q, r, associated_json, exists[0]))
            else:
                cursor.execute("""
                    INSERT INTO chronology_events (year, end_year, name, description, global_q, global_r, associated_entities_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (year, end_year, name, desc, q, r, associated_json))
                
            conn.commit()
            conn.close()
            self.load_db() # Sync state back to memory
            self.refresh_events_list()
            QMessageBox.information(self, "Success", "Event successfully saved to history chronicle!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save event: {e}")

    def delete_selected_event(self):
        selected = self.table_events.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        year = int(self.table_events.item(row, 0).text())
        name = self.table_events.item(row, 2).text()
        
        reply = QMessageBox.question(self, "Delete Event", f"Are you sure you want to delete event '{name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chronology_events WHERE year = ? AND name = ?", (year, name))
                conn.commit()
                conn.close()
                self.load_db() # Sync state back to memory
                self.refresh_events_list()
                QMessageBox.information(self, "Success", "Event successfully deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete event: {e}")

    def on_event_row_selected(self):
        selected = self.table_events.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        coords_str = self.table_events.item(row, 3).text()
        try:
            q, r = [int(c.strip()) for c in coords_str.split(",")]
            self.map_viewer.select_hex(q, r)
            self.selected_coord = (q, r)
            self.on_hex_selected(q, r)
        except Exception as e:
            print(f"[-] Map centering failed: {e}")
            
        # Unified Lore Integration: Check for associated notes
        event_name = self.table_events.item(row, 2).text()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT associated_entities_json FROM chronology_events WHERE name = ? AND year = ?", 
                           (event_name, int(self.table_events.item(row, 0).text())))
            res = cursor.fetchone()
            conn.close()
            if res and res[0]:
                notes = json.loads(res[0])
                if notes:
                    note_name = notes[0]
                    # Recursive tree search
                    def select_tree_item(parent_item):
                        for i in range(parent_item.childCount()):
                            child = parent_item.child(i)
                            if child.text(0) == note_name:
                                self.tree_notes.setCurrentItem(child)
                                self.load_selected_note()
                                return True
                            if select_tree_item(child):
                                return True
                        return False
                        
                    for i in range(self.tree_notes.topLevelItemCount()):
                        top_item = self.tree_notes.topLevelItem(i)
                        if select_tree_item(top_item):
                            self.left_sidebar_list.setCurrentRow(13) # Switch to Lore Notes editor page
                            break
        except Exception as ex:
            print(f"[-] Linked note loading error: {ex}")

    # --- Moons configurator table helpers ---
    def populate_moons_table(self):
        self.table_moons.setRowCount(0)
        moons = self.worldsmith_config.get("moons", [])
        for r_idx, m in enumerate(moons):
            self.table_moons.insertRow(r_idx)
            self.table_moons.setItem(r_idx, 0, QTableWidgetItem(m.get("name", "Moon")))
            self.table_moons.setItem(r_idx, 1, QTableWidgetItem(str(m.get("orbital_period", 28.0))))
            self.table_moons.setItem(r_idx, 2, QTableWidgetItem(m.get("luminescence_color", "#FFFFFF")))

    def on_add_moon_row(self):
        row = self.table_moons.rowCount()
        self.table_moons.insertRow(row)
        self.table_moons.setItem(row, 0, QTableWidgetItem(f"Luna {row+1}"))
        self.table_moons.setItem(row, 1, QTableWidgetItem("30.0"))
        self.table_moons.setItem(row, 2, QTableWidgetItem("#FFFFFF"))

    def on_del_moon_row(self):
        selected = self.table_moons.selectedItems()
        if selected:
            self.table_moons.removeRow(selected[0].row())

    # --- AI Placers & Assist Board Methods ---
    def suggest_map_placements(self):
        self.txt_ai_advice.setPlainText("AI is analyzing map topography, elevation centroids, and factions... Please wait...")
        self.worker = self.start_ai_task("ai_suggest_placements")
        self.worker.finished.connect(self.on_suggest_placements_finished)
        
    def on_suggest_placements_finished(self, result):
        if result.get("success"):
            self.last_placements_data = result["data"]
            
            # Map glowing target pins drawing
            pins = []
            text = "<h3>Suggested Map Placements & Border Diplomacy</h3>"
            for p in self.last_placements_data.get("placements", []):
                pins.append((p["q"], p["r"], p["name"]))
                text += f"<b>Place {p['type'].capitalize()}:</b> {p['name']} at ({p['q']}, {p['r']}) - <i>{p['reason']}</i><br>"
                
            self.map_viewer.suggested_pins = pins
            self.map_viewer.load_map(self.state)
            
            text += "<h3>Suggested Diplomacy Status</h3>"
            for d in self.last_placements_data.get("diplomacy", []):
                text += f"Faction {d['faction_a_id']} vs Faction {d['faction_b_id']}: <b>{d['relation']}</b> - <i>{d['reason']}</i><br>"
            self.txt_ai_advice.setHtml(text)
            self.btn_apply_placements.setEnabled(True)
        else:
            self.txt_ai_advice.setPlainText(f"Failed: {result.get('error')}")
            
    def apply_suggested_placements(self):
        if not hasattr(self, "last_placements_data") or not self.last_placements_data:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for p in self.last_placements_data.get("placements", []):
                cursor.execute("SELECT id FROM global_hexes WHERE q = ? AND r = ?", (p["q"], p["r"]))
                h_row = cursor.fetchone()
                if h_row:
                    hex_id = h_row[0]
                    if p["type"] == "city":
                        cursor.execute("""
                            INSERT INTO settlements (name, global_hex_id, settlement_level, faction_id)
                            VALUES (?, ?, 3, ?)
                        """, (p["name"], hex_id, p.get("faction_id", 1)))
                    else:
                        cursor.execute("""
                            INSERT INTO markers (type, global_hex_id, name)
                            VALUES (?, ?, ?)
                        """, (p["type"].upper(), hex_id, p["name"]))
            conn.commit()
            conn.close()
            
            # Clear suggested pins
            self.map_viewer.suggested_pins = []
            self.load_db()
            self.map_viewer.load_map(self.state)
            
            QMessageBox.information(self, "Success", "AI placements successfully applied to the world map!")
            self.btn_apply_placements.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply placements: {e}")
            
    def suggest_timeline(self):
        self.txt_ai_advice.setPlainText("AI is scanning markdown notes to extract dates and organize the history timeline... Please wait...")
        self.worker = self.start_ai_task("ai_suggest_chronology")
        self.worker.finished.connect(self.on_suggest_chronology_finished)
        
    def on_suggest_chronology_finished(self, result):
        if result.get("success"):
            self.last_chronology_data = result["data"]
            text = "<h3>Suggested Organized History Timeline</h3>"
            for ev in self.last_chronology_data.get("events", []):
                text += f"<b>Yr {ev['year']}:</b> {ev['name']} - <i>{ev['description']}</i> (Hex: {ev['q']}, {ev['r']})<br>"
            self.txt_ai_advice.setHtml(text)
            self.btn_apply_timeline.setEnabled(True)
        else:
            self.txt_ai_advice.setPlainText(f"Failed: {result.get('error')}")
            
    def apply_suggested_timeline(self):
        if not hasattr(self, "last_chronology_data") or not self.last_chronology_data:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for ev in self.last_chronology_data.get("events", []):
                cursor.execute("""
                    INSERT INTO chronology_events (year, end_year, name, description, global_q, global_r)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ev["year"], ev["year"], ev["name"], ev["description"], ev["q"], ev["r"]))
            conn.commit()
            conn.close()
            self.refresh_events_list()
            QMessageBox.information(self, "Success", "Suggested events applied to database!")
            self.btn_apply_timeline.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply timeline: {e}")

    def suggest_cosmology(self):
        self.txt_ai_advice.setPlainText("AI is calculating stable moons and calendar divisions... Please wait...")
        self.worker = self.start_ai_task("ai_suggest_cosmology")
        self.worker.finished.connect(self.on_suggest_cosmology_finished)
        
    def on_suggest_cosmology_finished(self, result):
        if result.get("success"):
            data = result["data"]
            self.last_cosmology_data = data
            
            # Display suggestions
            text = "<h3>Suggested Balanced Cosmology Orbits</h3>"
            text += f"<b>Months per Year:</b> {data['calendar_settings']['months_per_year']}<br>"
            text += f"<b>Days per Month:</b> {data['calendar_settings']['days_per_month']}<br>"
            text += f"<b>Leap Days:</b> {data['calendar_settings']['leap_days']}<br><br>"
            
            text += "<b>Suggested Moons:</b><br>"
            for m in data.get("moons", []):
                text += f"- {m['name']}: orbital period {m['orbital_period']} days, luminescence {m['luminescence_color']}<br>"
            self.txt_ai_advice.setHtml(text)
        else:
            self.txt_ai_advice.setPlainText(f"Failed: {result.get('error')}")

    # --- Z-Dimension Selector ---
    def on_z_layer_changed(self):
        layer_map = {
            "Surface": "surface",
            "Sky Layer 1": "sky_1",
            "Sky Layer 2": "sky_2",
            "Subterranean U1": "underfloor_1",
            "Subterranean U2": "underfloor_2",
            "Leylines / Magic Layer": "magic"
        }
        txt = self.cb_z_layer.currentText()
        self.map_viewer.current_z_layer = layer_map.get(txt, "surface")
        self.map_viewer.load_map(self.state)

    # --- Save AI Config Matrix ---
    def save_ai_scope_settings(self):
        disabled = []
        if not self.chk_timeline.isChecked():
            disabled.append("chronological_timeline_gaps")
        if not self.chk_factions.isChecked():
            disabled.append("faction_currency_consistency")
        if not self.chk_climate.isChecked():
            disabled.append("geographical_hydrology_checks")
        if not self.chk_hydrology.isChecked():
            disabled.append("atmospheric_buffer_snapping")
            
        self.worldsmith_config["ai_auditor_settings"]["disabled_linators"] = disabled
        self.save_worldsmith_config()

    # --- Custom templates and layers registration ---
    def register_custom_layer(self):
        name = self.txt_layer_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid custom layer name.")
            return
            
        layer_id = "usr_lay_" + name.lower().replace(" ", "_")
        for layer in self.worldsmith_config["custom_layers"]:
            if layer["layer_id"] == layer_id:
                QMessageBox.critical(self, "Collision", "A custom layer with this ID already exists.")
                return
                
        self.worldsmith_config["custom_layers"].append({
            "layer_id": layer_id,
            "name": name,
            "type": "polygon_overlay",
            "attributes": []
        })
        self.save_worldsmith_config()
        self.cb_z_layer.addItem(name)
        QMessageBox.information(self, "Registered", f"Custom Map Layer '{name}' successfully registered!")
        self.txt_layer_name.clear()

    def inject_custom_field(self):
        template = self.cb_target_template.currentText()
        field = self.txt_field_name.text().strip()
        f_type = self.cb_field_type.currentText()
        required = self.chk_field_required.isChecked()
        
        if not field:
            QMessageBox.warning(self, "Invalid Field Name", "Please enter a valid field name.")
            return
            
        if template not in self.worldsmith_config["custom_templates"]:
            self.worldsmith_config["custom_templates"][template] = []
            
        # Check collision
        for existing in self.worldsmith_config["custom_templates"][template]:
            if existing["fieldName"] == field:
                QMessageBox.critical(self, "Collision", "Field already defined for this template.")
                return
                
        self.worldsmith_config["custom_templates"][template].append({
            "fieldName": field,
            "fieldType": f_type,
            "isRequired": required
        })
        self.save_worldsmith_config()
        QMessageBox.information(self, "Injected", f"Field '{field}' successfully added to template '{template}'!")
        self.txt_field_name.clear()

    # --- Magic Layer Brush ---
    def paint_magic_anomaly_tool(self):
        self.map_viewer.set_tool_mode("Paint Chaos", "LUX_ECLIPSE")
        self.lbl_magic_warnings.setText("Paint magical anomalies using soft gradient circles on the map.")

    def paint_leyline_anchor_tool(self):
        self.map_viewer.set_tool_mode("Paint River Volume", 10)
        self.lbl_magic_warnings.setText("Paint high volume leyline nodes directly onto coordinates.")

    # --- Override Hex Selection ---
    def on_hex_selected(self, q, r):
        super().on_hex_selected(q, r)
        hx = self.state.hexes.get((q, r))
        
        if hx and hx.settlement:
            self.load_city_map_view(hx.settlement.name)
        else:
            self.lbl_city_title.setText("<b>No Settlement Selected</b>")
            self.lbl_city_image.setPixmap(QPixmap())
            self.lbl_city_image.setText("Select a settlement on the map to view its city layout.")
            self.btn_regen_city.setEnabled(False)
            self.current_city_name = None
            self.current_city_seed = None
            
        self.update_constellations_visibility()
        self.update_inspect_display(q, r)

    # --- Temporal Engine Year Slider ---
    def on_timeline_changed(self):
        year = self.slider_timeline.value()
        self.lbl_timeline_year.setText(f"Year: {year}")
        self.map_viewer.current_year = year
        self.map_viewer.load_map(self.state)
        self.check_lunar_conjunctions()
        self.celestial_preview.update()
        if self.cb_seasonal_tilt.isChecked():
            self.apply_seasonal_tilt()
        # Keep left panel coordinate selection context updated
        if self.selected_coord:
            self.on_hex_selected(*self.selected_coord)

    # --- Cosmovision Selector ---
    def on_narrator_changed(self):
        idx = self.cb_narrator.currentIndex()
        profile_id = self.cb_narrator.itemData(idx)
        if not profile_id:
            self.map_viewer.name_overrides = {}
        else:
            narrators = self.worldsmith_config.get("unreliable_narrators", [])
            profile = next((n for n in narrators if n["profile_id"] == profile_id), None)
            if profile:
                self.map_viewer.name_overrides = profile.get("name_overrides", {})
            else:
                self.map_viewer.name_overrides = {}
        self.map_viewer.load_map(self.state)

    # --- Epidemiology Simulator ---
    def paint_outbreak_tool(self):
        self.map_viewer.set_tool_mode("Paint Chaos", "WARP_STORM")
        self.lbl_disease_status.setText("Paint outbreak zones on the map canvas.")

    def run_disease_step(self):
        infected = []
        for (q, r), hx in self.state.hexes.items():
            if hx.chaos_domain:
                infected.append((q, r))
                
        mode = self.cb_transmission.currentText()
        new_infections = []
        
        if mode == "Airborne (Wind-Bound)":
            for q, r in infected:
                hx = self.state.hexes.get((q, r))
                w_dir = hx.wind_direction if hx else "NE"
                vecs = {'SW': (-1, 1), 'NE': (1, -1), 'NW': (-1, -1)}
                dx, dy = vecs.get(w_dir, (1, -1))
                nq, nr = q + dx, r + dy
                if (nq, nr) in self.state.hexes and not self.state.hexes[(nq, nr)].chaos_domain:
                    new_infections.append((nq, nr))
        elif mode == "Commercial (Trade-Bound)":
            for route in self.state.routes:
                h_a = None
                h_b = None
                for (q, r), hx in self.state.hexes.items():
                    if hx.settlement:
                        if hx.settlement.id == route.settlement_a_id:
                            h_a = (q, r)
                        elif hx.settlement.id == route.settlement_b_id:
                            h_b = (q, r)
                if h_a and h_b:
                    if h_a in infected and h_b not in infected:
                        new_infections.append(h_b)
                    elif h_b in infected and h_a not in infected:
                        new_infections.append(h_a)
        elif mode == "Vermin-Vector (Terrain-Bound)":
            from python_fmg.core.grid import get_neighbors
            for q, r in infected:
                for nq, nr in get_neighbors(q, r):
                    if (nq, nr) in self.state.hexes:
                        nh = self.state.hexes[(nq, nr)]
                        if nh.elevation < 12 and nh.biome != 8 and not nh.chaos_domain:
                            if random.random() < 0.6:
                                new_infections.append((nq, nr))
        elif mode == "Magical Vector (Leyline-Bound)":
            for q, r in infected:
                curr_h = self.state.hexes[(q, r)]
                if curr_h.res >= 50000:
                    for (nq, nr), nh in self.state.hexes.items():
                        if nh.res >= 50000 and not nh.chaos_domain:
                            if random.random() < 0.4:
                                new_infections.append((nq, nr))
                                
        for q, r in new_infections:
            self.state.hexes[(q, r)].chaos_domain = "WARP_STORM"
            
        self.map_viewer.load_map(self.state)
        self.lbl_disease_status.setText(f"Outbreak step simulated. {len(new_infections)} new hexes infected.")
        # Keep left panel coordinate selection context updated
        if self.selected_coord:
            self.on_hex_selected(*self.selected_coord)

    def check_lunar_conjunctions(self):
        day = self.slider_timeline.value()
        moons = self.worldsmith_config.get("moons", [])
        phases = []
        for m in moons:
            name = m["name"]
            period = m["orbital_period"]
            color = m["luminescence_color"]
            phase_pct = (day % period) / period
            if phase_pct < 0.15 or phase_pct > 0.85: phase = "NEW"
            elif phase_pct < 0.35: phase = "WAXING CRESCENT"
            elif phase_pct < 0.65: phase = "FULL"
            else: phase = "WANING CRESCENT"
            phases.append(f"<font color='{color}'><b>{name}</b></font>: {phase}")
        self.lbl_lunar_status.setText("<h3>Orbits</h3>" + "<br>".join(phases))

    def apply_seasonal_tilt(self):
        day = self.slider_timeline.value()
        cal = self.worldsmith_config.get("calendar_settings", {})
        year_length = (cal.get("months_per_year", 12) * cal.get("days_per_month", 30))
        
        phase = math.sin((day % year_length) / year_length * 2 * math.pi)
        
        for hx in self.state.hexes.values():
            base_temp = hx.p2
            hx.p2 = max(0, min(255, int(base_temp + phase * 25)))
        self.map_viewer.load_map(self.state)

    # --- Astronomy Horizon Visibility ---
    def update_constellations_visibility(self):
        if not self.map_viewer.selected_item:
            self.lbl_visible_constellations.setText("Select a coordinate to check constellation horizon visibility.")
            return
            
        r = self.map_viewer.selected_item.r
        latitude = r / 26.0
        
        visible = []
        if latitude < 0.3:
            visible.append("The Great Dragon (North Sky)")
        elif latitude > 0.7:
            visible.append("The Abyss Leviathan (South Sky)")
        else:
            visible.append("The Hunter (Equatorial Sky)")
            visible.append("The Astral Scale")
            
        self.lbl_visible_constellations.setText("<b>Visible Sky Dome:</b><br>" + ", ".join(visible))

    # --- Reverse Cartography Batch Importer ---
    def run_reverse_cartography(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder of Lore Notes to Reverse-Engineer")
        if folder_path:
            self.statusBar().showMessage("Reverse Cartography Pipeline running...")
            self.rc_worker = ReverseCartographyWorker(folder_path, self.db_path)
            self.rc_worker.finished.connect(self.on_reverse_cartography_finished)
            self.rc_worker.start()

    def on_reverse_cartography_finished(self, result):
        self.statusBar().showMessage("Ready.")
        if result["success"]:
            QMessageBox.information(self, "Success", f"Reverse Cartography complete! Processed {result['count']} files and populated the map grid.")
            self.load_db()
            self.map_viewer.load_map(self.state)
        else:
            QMessageBox.critical(self, "Error", f"Reverse Cartography failed: {result['error']}")

    # --- Procedural City Map View ---
    def load_city_map_view(self, name, seed_val=None):
        self.current_city_name = name
        if seed_val is None:
            self.current_city_seed = f"{name}_seed"
        else:
            self.current_city_seed = seed_val
            
        safe_name = name.lower().replace(" ", "_").replace("-", "_")
        illus_dir = str(paths.ASSETS_DIR / "illustrations")
        os.makedirs(illus_dir, exist_ok=True)
        city_map_path = os.path.join(illus_dir, f"city_map_{safe_name}.png")
        
        try:
            generate_city_map(name, self.current_city_seed, city_map_path)
            
            pix = QPixmap(city_map_path)
            scaled_pix = pix.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_city_image.setPixmap(scaled_pix)
            self.lbl_city_title.setText(f"<b>Layout of {name}</b>")
            self.btn_regen_city.setEnabled(True)
        except Exception as e:
            self.lbl_city_image.setText(f"Failed to generate layout: {e}")
            self.btn_regen_city.setEnabled(False)

    def regenerate_current_city(self):
        if not self.current_city_name:
            return
        new_seed = f"{self.current_city_name}_seed_{random.randint(0, 100000)}"
        self.load_city_map_view(self.current_city_name, new_seed)

    # --- Worker Thread Managers ---
    def start_worker(self, worker):
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Busy", "Another background process is currently running. Please wait.")
            return False
            
        self.current_worker = worker
        self.current_worker.finished.connect(self.on_worker_finished)
        self.statusBar().showMessage("Processing background task...")
        self.current_worker.start()
        return True

    def run_verification(self):
        worker = OllamaWorker("verify")
        self.start_worker(worker)

    def run_vault_forge(self):
        worker = OllamaWorker("forge")
        self.start_worker(worker)

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if file_path:
            self.txt_img_path.setText(file_path)

    def ingest_image(self):
        temp_path = self.txt_img_path.text().strip()
        description = self.txt_img_desc.text().strip()
        subject = self.cb_img_subject.currentText().strip()
        
        if not temp_path or not os.path.exists(temp_path):
            QMessageBox.critical(self, "Error", "Invalid or missing image file path.")
            return
        if not description or not subject:
            QMessageBox.critical(self, "Error", "Description and Subject must be specified.")
            return
            
        payload = {
            "temp_path": temp_path,
            "description": description,
            "subject": subject
        }
        worker = OllamaWorker("ingest_image", payload)
        self.start_worker(worker)

    def on_worker_finished(self, result):
        self.statusBar().showMessage("Ready.")
        if not result.get("success"):
            QMessageBox.critical(self, "Background Process Error", result.get("error", "An unknown error occurred."))
            return
            
        task = result.get("task")
        
        if task == "verify":
            status = result["status"]
            self.progress_bar.setValue(status["progress"])
            
            self.active_problems = status["errors"] + status["gaps"]
            self.gaps_table.setRowCount(0)
            
            for p in self.active_problems:
                row = self.gaps_table.rowCount()
                self.gaps_table.insertRow(row)
                p_type = "ERROR" if p in status["errors"] else "GAP"
                self.gaps_table.setItem(row, 0, QTableWidgetItem(p["subject"]))
                self.gaps_table.setItem(row, 1, QTableWidgetItem(p_type))
                self.gaps_table.setItem(row, 2, QTableWidgetItem(p["question"]))
                
            self.cb_img_subject.clear()
            ontology = result["ontology"]
            for s_name in sorted(ontology["subjects"].keys()):
                self.cb_img_subject.addItem(s_name)
                
            self.lbl_resolve_question.setText("Select an issue above to clarify.")
            self.text_resolve_answer.clear()
            self.btn_submit_clarification.setEnabled(False)
            
        elif task == "forge":
            QMessageBox.information(self, "Forge Vault", f"Successfully forged {len(result['files'])} wiki notes!\nDefinitive 2D medieval city layout maps and regional crops have been dynamically generated and embedded.")
            
        elif task == "ingest_image":
            QMessageBox.information(self, "Image Ingested", f"Successfully ingested image '{result['filename']}'. Note has been updated.")
            self.txt_img_path.clear()
            self.txt_img_desc.clear()
            self.run_verification()
            
        elif task == "ai_classify_note":
            self.btn_auto_tag.setEnabled(True)
            new_cat = result.get("category", "people")
            
            # Move file physically to new folder
            import lore_forge
            if self.current_note_path and os.path.exists(self.current_note_path):
                subj_name = os.path.basename(os.path.dirname(self.current_note_path))
                new_dir = os.path.join(lore_forge.LORE_DB, new_cat, subj_name)
                os.makedirs(new_dir, exist_ok=True)
                new_path = os.path.join(new_dir, os.path.basename(self.current_note_path))
                try:
                    shutil.move(self.current_note_path, new_path)
                    self.current_note_path = new_path
                    self.lbl_editing_file.setText(f"Editing: {new_cat}/{subj_name}/{os.path.basename(new_path)}")
                    QMessageBox.information(self, "Categorized", f"AI successfully auto-categorized note under folder: {new_cat}")
                    self.refresh_notes_list()
                except Exception as ex:
                    QMessageBox.critical(self, "Move Failed", f"Failed to move file: {ex}")
                    
        elif task == "ai_suggest_inquiries":
            self.lbl_ai_inquiry.setText(result.get("response", "No prompts returned."))

    # --- Gap Selection and Resolution ---
    def on_gap_selected(self):
        row = self.gaps_table.currentRow()
        if 0 <= row < len(self.active_problems):
            prob = self.active_problems[row]
            self.lbl_resolve_question.setText(f"<b>{prob['subject']} ({prob['category']}):</b><br>{prob['question']}")
            self.text_resolve_answer.clear()
            self.btn_submit_clarification.setEnabled(True)
            self.btn_ai_draft.setEnabled(True)
        else:
            self.lbl_resolve_question.setText("Select an issue above to clarify.")
            self.btn_submit_clarification.setEnabled(False)
            self.btn_ai_draft.setEnabled(False)

    def submit_clarification(self):
        row = self.gaps_table.currentRow()
        if 0 <= row < len(self.active_problems):
            prob = self.active_problems[row]
            answer = self.text_resolve_answer.toPlainText().strip()
            
            if not answer:
                QMessageBox.warning(self, "Empty Answer", "Please type a clarification before submitting.")
                return
                
            import lore_forge
            subj_dir = os.path.join(lore_forge.LORE_DB, prob['category'], prob['subject'])
            os.makedirs(subj_dir, exist_ok=True)
            clar_file = os.path.join(subj_dir, "clarifications.md")
            
            try:
                with open(clar_file, "a", encoding="utf-8") as f:
                    f.write(f"\n### Clarification ({prob['field']})\n{answer}\n")
                self.run_verification()
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Failed to save clarification: {e}")

    # --- Data Export Methods ---
    def export_web_wiki(self):
        try:
            import compile_web_wiki
            success = compile_web_wiki.compile_wiki_manifest()
            if success:
                QMessageBox.information(self, "Success", "Web wiki slides manifest compiled successfully!")
            else:
                QMessageBox.critical(self, "Error", "Web wiki compilation failed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compile web wiki: {e}")

    def export_worldbuilder_json(self):
        output_path, _ = QFileDialog.getSaveFileName(self, "Export World Data to JSON", "", "JSON Files (*.json)")
        if output_path:
            import export_data_formats
            success, msg = export_data_formats.export_to_json(self.db_path, output_path)
            if success:
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.critical(self, "Error", msg)

    def export_geojson(self):
        output_path, _ = QFileDialog.getSaveFileName(self, "Export Boundaries to GeoJSON", "", "GeoJSON Files (*.geojson)")
        if output_path:
            import export_data_formats
            success, msg = export_data_formats.export_to_geojson(self.db_path, output_path)
            if success:
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.critical(self, "Error", msg)

    # --- Subclassed Override Editors ---
    def open_provinces_editor(self):
        self.left_sidebar_list.setCurrentRow(4)
        
    def open_religions_editor(self):
        self.left_sidebar_list.setCurrentRow(5)
        
    def open_cultures_editor(self):
        self.left_sidebar_list.setCurrentRow(6)
        
    def open_chaos_editor(self):
        self.left_sidebar_list.setCurrentRow(7)
        
    def open_settlements_directory(self):
        self.left_sidebar_list.setCurrentRow(8)
        
    def open_names_editor(self):
        self.left_sidebar_list.setCurrentRow(9)
        
    def open_markers_editor(self):
        self.left_sidebar_list.setCurrentRow(10)
        
    def open_forces_editor(self):
        self.left_sidebar_list.setCurrentRow(11)
        
    def open_routes_editor(self):
        self.left_sidebar_list.setCurrentRow(12)

    def open_elevation_editor(self):
        self.left_sidebar_list.setCurrentRow(1)

    def open_biomes_editor(self):
        self.left_sidebar_list.setCurrentRow(2)

    def open_factions_editor(self):
        self.left_sidebar_list.setCurrentRow(3)

    def run_sim_tick(self):
        current_year = self.slider_timeline.value()
        if current_year < 3000:
            self.slider_timeline.setValue(current_year + 1)
            self.statusBar().showMessage(f"Advanced timeline year to {current_year + 1}", 3000)
        else:
            QMessageBox.information(self, "Timeline Limit", "Reached end of chronological timeline bounds.")

    def load_db(self):
        if not os.path.exists(self.db_path):
            QMessageBox.critical(self, "Error", f"Worldsmith DB not found at: {self.db_path}")
            return
            
        from python_fmg.core.db_sync import load_from_db
        state = load_from_db(self.db_path)
        if state:
            self.state = state
            self.map_viewer.load_map(self.state)
            self.update_factions_ui()
            self.update_provinces_ui()
            self.update_entities_ui()
            self.update_routes_ui()
            self.update_religions_ui()
            self.update_cultures_ui()
            self.update_markers_ui()
            self.update_settlements_directory_ui()
            self.update_culture_names_ui()
            self.statusBar().showMessage("Successfully loaded map state from worldsmith DB.", 3000)
        else:
            QMessageBox.critical(self, "Error", "Failed to parse map from database.")
            
    def save_db(self):
        try:
            from python_fmg.core.db_sync import save_to_db
            save_to_db(self.state, self.db_path)
            self.statusBar().showMessage("Successfully synchronized state to worldsmith DB.", 3000)
            QMessageBox.information(self, "Success", "World State synced successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save to database:\n{e}")

    def on_sett_name_changed(self):
        super().on_sett_name_changed()
        if self.selected_coord:
            hx = self.state.hexes.get(self.selected_coord)
            if hx and hx.settlement:
                self.load_city_map_view(hx.settlement.name)
