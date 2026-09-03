import os
from pathlib import Path

try:
    from llama_cpp import Llama
except ImportError:  # pragma: no cover
    Llama = None  # type: ignore

class AIDirector:
    """Wraps a local GGUF model using llama-cpp-python.

    Provides compatible ``parse_intent``, ``generate_llm_prompt``, and Reactive Seed generation.
    Expects a ``models`` folder with a ``*.gguf`` file.
    """

    def __init__(self, model_path: str | os.PathLike = None):
        default_dir = Path(__file__).resolve().parents[1] / "models"
        if model_path is None:
            candidates = list(default_dir.glob("*.gguf"))
            if not candidates:
                raise FileNotFoundError(
                    f"No GGUF model found in {default_dir}. Place a .gguf model file there."
                )
            model_path = candidates[0]
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        try:
            self._llama = Llama(
            model_path=str(self.model_path),
            n_ctx=512,
            n_threads=2,
            n_gpu_layers=0,
            verbose=True,
        )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            with open("llama_error_log.txt", "w") as f:
                f.write(f"FAILED TO INIT LLAMA:\n{error_details}")
            print(f"\n\n[CRITICAL ERROR IN LLAMA INIT]: {e}")
            
            # Fallback to a dummy no-op Llama implementation to prevent crash
            class _DummyLlama:
                def __call__(self, *args, **kwargs):
                    return {"choices": [{"text": "[Model failed to initialize]"}]}
            self._llama = _DummyLlama()
            
        self.system_prompt = (
            "SYSTEM DIRECTIVE: You are the autonomous Game Director and Narrative Engine for Project S.A.G.A., "
            "a gritty tabletop roleplaying game set in the ruined, drift-warped world of Okasha. "
            "Your purpose is to immerse the player, weave organic story seeds naturally into scene descriptions, "
            "and enforce mechanical consequences without breaking character. Never break the fourth wall. "
            "Never act as an assistant; you are the world and its narrator. "
            "STRICT GENRE: This is a Gritty Black-Powder Fantasy world. STRICTLY NO sci-fi, no spaceships, no lasers, no modern technology."
        )

    def parse_intent(self, intent_raw: str) -> dict:
        parts = intent_raw.split()
        target = parts[0] if parts else ""
        return {"target": target}

    def extract_anomaly_equation(self, intent_raw: str) -> str:
        """
        Uses the LLM to parse a spoken spell into the BRUTAL Engine Anomaly Equation.
        Returns a JSON string.
        """
        prompt = (
            "You are a rule parser for the BRUTAL RPG Engine. The player is casting an Anomaly (magic spell).\n"
            "Extract the spell parameters into this exact JSON format:\n"
            "{\n"
            '  "shape": "[point, line, cone, burst, wall, or aura]",\n'
            '  "school": "[Mass, Ordo, Motus, Flux, Vita, Nexus, Anumis, Ratio, Lux, Omen, Aura, or Lex]",\n'
            '  "effect_rank": [1 to 10],\n'
            '  "power_scale": [1 to 10]\n'
            "}\n\n"
            f"Player spell: '{intent_raw}'\n"
            "Output ONLY the JSON:\n"
        )
        
        output = self._llama(
            prompt,
            max_tokens=64,
            temperature=0.1,
            top_p=0.9,
            stop=["}"],
        )
        
        raw_text = output.get("choices", [{}])[0].get("text", "").strip()
        # Add the closing brace since it was used as a stop token
        if "{" in raw_text and not raw_text.endswith("}"):
            raw_text += "\n}"
            
        return raw_text

    def generate_llm_prompt(self, mechanical_result: str, context: str, intent_raw: str = None, filters: str = "") -> str:
        action_directive = ""
        if intent_raw:
            if "talk to" in intent_raw.lower():
                action_directive = f"The player's action is: '{intent_raw}'. CRITICAL: Generate the NPC's direct spoken dialogue in quotes, responding in character. Do not just describe the scene.\n"
            else:
                action_directive = f"The player's action is: '{intent_raw}'.\n"
                
        full_prompt = (
            f"<|system|>\n{self.system_prompt}\n"
            f"{'STRICT CONTENT FILTER: Do NOT include any themes of ' + filters + ' under any circumstances.' if filters else ''}\n<|end|>\n"
            f"<|user|>\n"
            f"Context & World State:\n{context}\n\n"
            f"Mechanical Result / Action Resolution:\n{mechanical_result}\n"
            f"Player Intent: {intent_raw if intent_raw else 'Observing'}\n\n"
            f"CRITICAL DIRECTIVE:\n"
            f"1. Describe the outcome of the player's action concisely.\n"
            f"2. Explicitly detail 1 to 3 interactive points of interest (an NPC, an object, or an exit path) to keep the scene engaging.\n"
            f"3. End your response with an immediate consequence, threat, or by asking 'What do you do?'\n"
            f"4. Do NOT just describe empty scenery.\n"
            f"{action_directive}\n"
            f"<|end|>\n"
            f"<|assistant|>\n"
        )
        output = self._llama(
            full_prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=["\n\n"],
        )
        return output.get("choices", [{}])[0].get("text", "").strip()

    def build_director_prompt_with_spine(self, location_name: str, local_lore: str, subtle_seeds: list, campaign_weaver, filters: str = "") -> str:
        """Constructs a scene description prompt incorporating reactive seeds and the campaign spine organically."""
        seed_whispers = "\n".join([f"- [ENVIRONMENTAL DETAIL] {seed.subtle_description}" for seed in subtle_seeds])
        
        history_summary = "\n".join([f"- Past Action: {h['node']} resulted in '{h['action_taken']}'" for h in campaign_weaver.get_resolved_history(5)])
        escalated_threads = campaign_weaver.get_escalated_threads()
        escalations = "\n".join([f"- Unresolved Threat: {e}" for e in escalated_threads])
        
        full_prompt = (
            f"<|system|>\n{self.system_prompt}\n"
            f"{'STRICT CONTENT FILTER: Do NOT include any themes of ' + filters + ' under any circumstances.' if filters else ''}\n<|end|>\n"
            f"<|user|>\n"
            f"LOCATION: {location_name}\n"
            f"CAMPAIGN ACT: Act {campaign_weaver.get_campaign_act()}\n"
            f"LORE: {local_lore}\n\n"
            f"ACCUMULATED PLAYER HISTORY (The Campaign Spine):\n"
            f"{history_summary if history_summary else 'The journey is just beginning; the world is a blank slate.'}\n\n"
            f"ESCALATING WORLD CONSEQUENCES:\n"
            f"{escalations if escalations else 'None currently threatening.'}\n\n"
            f"SUBTLE LOCAL SEEDS AVAILABLE:\n"
            f"{seed_whispers if seed_whispers else 'None'}\n\n"
            f"CRITICAL DIRECTIVE: \n"
            f"1. Establish the scene clearly (Inside/Outside, Lighting, Atmosphere).\n"
            f"2. Weave in the consequences of past player choices naturally.\n"
            f"3. CRITICAL: You MUST explicitly describe 1 to 3 interactive points of interest (e.g., an NPC looking at them, a strange machine, an open door).\n"
            f"4. End your narration with an immediate hook, danger, or the question 'What do you do?'\n"
            f"5. Do NOT generate empty scenery without purpose.\n"
            f"<|end|>\n"
            f"<|assistant|>\n"
        )
        
        output = self._llama(
            full_prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=["\n\n"],
        )
        return output.get("choices", [{}])[0].get("text", "").strip()

    def evaluate_action_for_seed(self, intent_raw: str, mechanical_result: str) -> str:
        """Analyzes an action to see if it generates a new Reactive Seed."""
        prompt = (
            "You are evaluating a player's action for consequences in a living RPG world.\n"
            f"Action: {intent_raw}\n"
            f"Result: {mechanical_result}\n\n"
            "If this action caused a localized consequence (e.g., leaving an NPC unconscious, breaking a door, stealing an item), output a JSON block for a Reactive Seed.\n"
            "If it was a mundane action with no lingering consequence, output exactly: NONE.\n\n"
            "JSON Format:\n"
            "{\n"
            '  "origin_action": "brief description of what they did",\n'
            '  "subtle_description": "A subtle environmental clue that something changed (e.g., blood on the floor, a nervous guard, a missing component).",\n'
            '  "target_entity": "The person or object affected"\n'
            "}\n"
            "Output ONLY the JSON or NONE:\n"
        )
        
        output = self._llama(
            prompt,
            max_tokens=128,
            temperature=0.1,
            top_p=0.9,
            stop=["}"],
        )
        
        raw_text = output.get("choices", [{}])[0].get("text", "").strip()
        if raw_text == "NONE":
            return None
            
        if "{" in raw_text and not raw_text.endswith("}"):
            raw_text += "\n}"
            
        return raw_text
