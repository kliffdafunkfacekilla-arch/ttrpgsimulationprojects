# SAGA Project Specification & Blueprint
*Synthesized by: The Technical Writer (Updated with User Feedback)*

## 1. Vision & Goals
SAGA is a local, AI-driven TTRPG application. It acts as a software Dungeon Master, utilizing local LLMs to generate narrative content, manage a custom ruleset/world, and translate natural language/speech into game mechanics.
**Core Objectives:**
- Zero cloud dependency (100% local execution).
- Voice and Mouse support (STT/TTS).
- Persistent, dynamic world for long-term multi-session play.

## 2. Current State (Alpha) vs. Required State (Beta)
**The Problem:** The current Alpha relies heavily on synchronous execution and a `.json` file (`scene_state.json`) for Inter-Process Communication between the AI background loop and the PyQt UI. This causes bottlenecks, UI freezes during long LLM generations, and fragile state management.

**The Solution:** Transition to a completely decoupled, event-driven architecture using the "Forge vs. Game Master" pattern. 

## 3. Architectural Blueprint

### 3.1 Asynchronous Event Loop
- Integrate `qasync` to bridge Python's `asyncio` with the `PyQt6` event loop.
- All heavy operations (LLM Inference, TTS Generation, STT processing) must run as non-blocking async tasks or background `QThread` workers communicating via signals/slots.
- Eliminate `scene_state.json` file polling entirely in favor of direct memory state management.

### 3.2 System Decoupling
- **The Forge (Core Engine):** A strict Python layer managing the world state, player sheets, and mechanics. All data structures must be refactored into `Pydantic` models for strict typing and easy serialization.
- **The Game Master (AI Services):** Leverage the **existing built-in local AI model** (`phi-3` via `llama-cpp-python`). Instead of relying on a standalone 3rd-party microservice like Ollama, the built-in model will be wrapped in an asynchronous background thread or internal server. This keeps the model tightly bundled while preventing UI freezes. Feed it constrained, serialized Pydantic JSON to prevent hallucinations.
- **Memory & Storage:** Transition long-term narrative memory to a local vector database (like `ChromaDB` or `FAISS`) to enable RAG (Retrieval-Augmented Generation) for infinite campaign memory.

### 3.3 Folder Structure
The Beta transition will adopt the following modular structure:
```text
/beta_build
  /core            # Game mechanics, Pydantic models, Rules Engine
  /ui              # PyQt6 Views, qasync integrations
  /ai_services     # Built-in LLM wrappers, Prompt Engineering, RAG
  /audio           # Async STT / TTS managers
  /data            # SQLite / Vector DB storage
  /assets          # UI graphics, sprites, audio files
```

## 4. Next Steps
Once this specification is approved, The Architect will generate `beta_roadmap.json` and physically scaffold the `/beta_build` directory.
