# SAGA Project Audit Report

## 1. Project Goal
Based on `_archived/IDEA.md`, the ultimate goal is to build an AI-powered TTRPG application for local group play. Key features include:
- An AI Dungeon Master (DM)
- A simulated dynamic world
- A robust rule engine
- A story/campaign generator

## 2. Codebase Overview
The project currently resides in the `_archived` folder and consists of numerous disparate attempts, prototypes, and partial merges of the above features.

### Key Functional Areas & Corresponding Folders:
*   **Unified Applications / Merges:**
    *   `SAGA_Unified`: A highly organized, event-driven desktop app (PyQt6) combining core mechanics, UI, AI director, vector memory (ChromaDB), and audio services. Features a comprehensive `MIGRATION_SUMMARY.md`.
    *   `SAGA_Complete_Edition`: Contains `AI_Director`, `Backend`, and `FMG` folders.
    *   `SAGA_Combined`: Contains a quest system, effect engine, and external world DB integration.
*   **AI Directors & DM Assistants:**
    *   `aidm2`, `GMAI`, `DMAI`: Contain logic for AI DM interactions and NPC behaviors.
*   **World Generation & Mapping (VTT):**
    *   `fmg`, `fmg-rebuild_20260829_070201`, `Fantasy-Map-Generator`: Various versions of a Fantasy Map Generator, mostly web-based/JS.
    *   `worldsim`: Contains `omnis-generator` and legacy `shatterlands_simulator` files.
*   **Narrative & Campaign Logic (TaleWeaver):**
    *   `TALEWEAVERS_Clean_Upload`, `TALEWEAVERS2`, `TALEWEAVERS`: Contains campaign weavers, history ledgers, prompt templates, and character engines.
*   **Voice and Audio:**
    *   `SAGA_Voice`: Features Edge-TTS handler and STT integrations.
*   **Migration Scripts:**
    *   `asemble_and_push.py`: A script attempting to extract specific files into a headless engine structure called `shatterlands_simulator`.

## 3. Findings
- There is significant duplication of effort (e.g., multiple copies of SAGA, Taleweavers, and FMG).
- The most mature integration point appears to be `SAGA_Unified`, which successfully combines a desktop UI, basic voice I/O, core turn-based/combat logic, and LLM integrations.
- There is a split in technology stack: a rich Python backend/desktop-client ecosystem (SAGA, Taleweavers) and a web-based mapping/VTT ecosystem (FMG).

## 4. Merge Plan Details
To achieve a single functional project, we need a unified architecture. The plan is to extract the best, most recent components into the `DualStateEngine` directory.

### Target Architecture Structure (`DualStateEngine`)
*   **`backend/`**: The core simulation, rule engine, and AI.
    *   `core/` - Rules engine, turn management, combat math (from `SAGA_Unified/core`).
    *   `ai_director/` - DM logic, LLM worker, ChromaDB memory (from `SAGA_Unified/ai` and `GMAI/oracle.py`).
    *   `taleweaver/` - Quest generation, narrative history, world ledger (from `TALEWEAVERS_Clean_Upload` and `SAGA_Combined/quest`).
    *   `world_sim/` - Procedural world generation and reactive seeds.
    *   `audio/` - TTS and STT handling (from `SAGA_Unified/audio`).
    *   `data/` - SQLite databases, ChromaDB stores, assets.
    *   `api/` - A Flask/FastAPI interface to bridge the Python engine with a web VTT (as hinted by `requirements.txt` in `asemble_and_push.py`).
*   **`client_vtt/`**: The frontend UI and Map Generator.
    *   A web-based interface combining the map generation (from `fmg-rebuild`) with React/Vue components to talk to the Python backend.

### Execution Plan (High-Level)
1. Initialize the `DualStateEngine` folder with the target architecture.
2. Migrate the core Python rules and mechanics from `_archived/SAGA_Unified`.
3. Migrate the Taleweaver narrative components.
4. Setup the AI Director by merging `SAGA_Unified/ai` with any advanced logic in `_archived/GMAI` or `aidm2`.
5. Scaffold an API layer to allow a web-based VTT (like `fmg-rebuild`) to interact with the backend.
6. Centralize all configuration (`config/`) and dependencies (`requirements.txt`, `package.json`).
