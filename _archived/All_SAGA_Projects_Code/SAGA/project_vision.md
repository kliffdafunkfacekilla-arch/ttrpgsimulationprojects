# Project Vision: SAGA (Local AI-Driven TTRPG Platform)

## Overarching Vision
To create a fully local, immersive Tabletop Role-Playing Game (TTRPG) application powered by an AI-driven software Dungeon Master (DM). The platform will provide a deeply interactive, dynamically reactive world capable of supporting long-term, multi-session play for one or more players. 

## Primary Goals
1. **AI-Powered DM:** Utilize local Large Language Models (LLMs) to creatively generate narrative content, manage the world state, and interpret player inputs (both text and speech).
2. **Custom World & Ruleset:** Seamlessly integrate a bespoke ruleset and a rich, custom-built world that reacts and evolves based on player actions.
3. **Accessibility & Immersion:** 
   - **Speech-to-Text (STT) & Text-to-Speech (TTS):** Enable natural, voice-driven interaction for immersion.
   - **Mouse Control Support:** Provide intuitive UI interactions alongside text/voice inputs.
4. **Local Execution:** Ensure the entire stack (LLMs, TTS, STT, and game logic) runs locally to guarantee privacy, zero latency dependence on cloud APIs, and offline playability.
5. **Persistent Multi-Session Play:** Maintain a robust state management system that tracks long-term consequences, relationships, and world changes across multiple sessions.

## Core Focus for Beta Transition
The Beta phase will focus on solidifying the architecture to support these goals efficiently. This means untangling prototype code, establishing a robust local LLM pipeline (e.g., GGUF via llama.cpp), standardizing the UI/UX for mouse and voice inputs, and creating a scalable data structure for the dynamic world state.
