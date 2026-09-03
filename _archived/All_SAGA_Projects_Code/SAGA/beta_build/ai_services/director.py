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
    def __init__(self, model_path: str | os.PathLike = None, load_model: bool = True):
        default_dir = Path(__file__).resolve().parents[2] / "models"
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

        if load_model:
            try:
                self._llama = Llama(
                model_path=str(self.model_path),
                n_ctx=4096,
                n_threads=2,
                n_gpu_layers=0,  # Disabled GPU offloading to prevent access violation crashes
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
        else:
            self._llama = None
            
        self.system_prompt = (
            "SYSTEM DIRECTIVE: You are the autonomous Game Director and Narrative Engine for Project S.A.G.A., "
            "a gritty tabletop roleplaying game set in the ruined, drift-warped world of Okasha. "
            "Your purpose is to immerse the player, weave organic story seeds naturally into scene descriptions, "
            "and enforce mechanical consequences without breaking character. Never break the fourth wall. "
            "Never act as an assistant; you are the world and its narrator. "
            "STRICT GENRE: This is a Gritty Black-Powder Fantasy world. STRICTLY NO sci-fi, no spaceships, no lasers, no modern technology. "
            "CRITICAL: There are NO Humans, Elves, Dwarves, Orcs, or standard fantasy races in Okasha. DO NOT refer to the player or NPCs as such. "
            "If the species is unspecified, refer to them as mutants, beasts, or drifters."
        )

    def _get_scene_blueprint(self) -> str:
        """Reads the static pre-generated scene constraints to anchor the AI."""
        import json
        import os
        path = os.path.join("runtime_data", "current_scene.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                
                # Format clearly for the LLM
                output = "SCENE CONTEXT (DO NOT ALTER THIS):\n"
                if "visual_state" in data:
                    v = data["visual_state"]
                    output += f"- Lighting: {v.get('lighting', 'normal')}\n"
                    output += f"- Weather: {', '.join(v.get('weather_tags', []))}\n"
                if "narrative_constraints" in data:
                    n = data["narrative_constraints"]
                    output += f"- Plot Hook: {n.get('plot_hook', 'None')}\n"
                    if n.get("banned_elements"):
                        output += f"- BANNED ELEMENTS: {', '.join(n['banned_elements'])}\n"
                return output + "\n"
            except Exception:
                pass
        return ""

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
            f"{self._get_scene_blueprint()}"
            f"{'STRICT CONTENT FILTER: Do NOT include any themes of ' + filters + ' under any circumstances.' if filters else ''}\n<|end|>\n"
            f"<|user|>\n"
            f"Context & World State:\n{context}\n\n"
            f"Mechanical Result / Action Resolution:\n{mechanical_result}\n"
            f"Player Intent: {intent_raw if intent_raw else 'Observing'}\n\n"
            f"CRITICAL DIRECTIVE:\n"
            f"1. Describe the outcome of the player's action concisely.\n"
            f"2. INTERACTIVITY: Seamlessly weave 1 to 3 interactive points of interest (an NPC, an object, a path) into your prose. Do NOT list them with bullet points or numbers.\n"
            f"3. End your response with an immediate consequence, threat, or by asking 'What do you do?'\n"
            f"4. Do NOT just describe empty scenery.\n"
            f"{action_directive}\n"
            f"<|end|>\n"
            f"<|assistant|>\n"
        )
        output = self._llama(
            full_prompt,
            max_tokens=400,
            temperature=0.7,
            top_p=0.9,
        )
        return output.get("choices", [{}])[0].get("text", "").strip()

    def build_director_prompt_with_spine(self, location_name: str, local_lore: str, subtle_seeds: list, campaign_weaver, filters: str = "", intent_raw: str = None, mechanical_result: str = "", scene_script: str = "") -> str:
        """Constructs a scene description prompt incorporating reactive seeds and the campaign spine organically."""
        seed_whispers = "\n".join([f"- [ENVIRONMENTAL DETAIL] {seed.subtle_description}" for seed in subtle_seeds])
        
        history_summary = "\n".join([f"- Past Action: {h['node']} resulted in '{h['action_taken']}'" for h in campaign_weaver.get_resolved_history(5)])
        escalated_threads = campaign_weaver.get_escalated_threads()
        escalations = "\n".join([f"- Unresolved Threat: {e}" for e in escalated_threads])
        
        current_slot = campaign_weaver.get_current_slot()
        slot_directive = f"Act {current_slot['act']}, Step {current_slot['step']}: {current_slot['type']}" if current_slot else "Free Roam"
        
        slotted_seed_directive = ""
        if current_slot and current_slot.get('seed_id'):
            # The director must know what seed was locked into this slot
            slotted_seed_directive = "A specific interaction hook has been engaged by the player for this Step. You must grow this hook into the main objective of this scene."

        action_directive = ""
        if intent_raw:
            if "talk to" in intent_raw.lower():
                action_directive = f"The player's action is: '{intent_raw}'. CRITICAL: Generate the NPC's direct spoken dialogue in quotes, responding in character. Do not just describe the scene.\n"
            else:
                action_directive = f"The player's action is: '{intent_raw}'.\n"

        full_prompt = (
            f"<|system|>\n{self.system_prompt}\n"
            f"{self._get_scene_blueprint()}"
            f"{'STRICT CONTENT FILTER: Do NOT include any themes of ' + filters + ' under any circumstances.' if filters else ''}\n<|end|>\n"
            f"<|user|>\n"
            f"CURRENT CAMPAIGN SCRIPT: You are in {slot_directive}. You MUST align your narration with this specific story beat.\n"
            f"{slotted_seed_directive}\n"
            f"LOCATION: {location_name}\n"
            f"LORE: {local_lore}\n\n"
            f"BACKGROUND SCRIPT (READ THIS STRICTLY): \n"
            f"{scene_script}\n\n"
            f"ACCUMULATED PLAYER HISTORY (The Campaign Spine):\n"
            f"{history_summary if history_summary else 'The journey is just beginning; the world is a blank slate.'}\n\n"
            f"ESCALATING WORLD CONSEQUENCES:\n"
            f"{escalations if escalations else 'None currently threatening.'}\n\n"
            f"SUBTLE LOCAL SEEDS AVAILABLE:\n"
            f"{seed_whispers if seed_whispers else 'None'}\n\n"
            f"Mechanical Result / Action Resolution:\n{mechanical_result}\n\n"
            f"CRITICAL DIRECTIVE (SMART NARRATION PROTOCOL): \n"
            f"1. YOUR ROLE: You are essentially a prose-polisher for a mechanical 'madlibs' engine. Do NOT invent new lore, enemies, or subplots. Your ONLY job is to take the BACKGROUND SCRIPT, the mechanical result, the slotted seed, and weave them together into organic, logical prose.\n"
            f"2. READ THE SCRIPT: The BACKGROUND SCRIPT has already been written by the Story Manager. Use it as the foundation of your narration.\n"
            f"3. TONE: Be direct, gritty, and concise. Do NOT use flowery, overly poetic language or forced sensory metaphors.\n"
            f"4. BREVITY: Limit your narration to 2-3 punchy sentences (maximum 50-75 words). You are speaking to the player via voice audio, so be conversational and dramatic.\n"
            f"5. WEAVE SEEDS: If subtle seeds or escalations exist, mention them naturally and directly. If the slotted seed dictates the scene, make it the immediate focus.\n"
            f"6. INTERACTIVITY: You MUST seamlessly weave 1 to 3 interactive points of interest into your prose. Do NOT use bullet points, numbers, or labels like 'Interactive Point'.\n"
            f"7. MAP TRAVERSAL: If the current script step requires moving to a new area, provide clues or directions leading off-map.\n"
            f"8. AGENCY HANDOFF: End your narration with an immediate consequence, threat, or by asking 'What do you do?' to hand agency back to the player.\n"
            f"{action_directive}\n"
            f"<|end|>\n"
            f"<|assistant|>\n"
        )
        
        output = self._llama(
            full_prompt,
            max_tokens=500,
            temperature=0.72,
            top_p=0.9,
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

    def extract_scene_entities(self, scene_text: str) -> str:
        """
        Parses a generated scene description and extracts any physical entities (NPCs, props, hazards) 
        that the LLM hallucinated, outputting them as a JSON list for the VTT to spawn.
        """
        prompt = (
            "You are a parsing engine for a virtual tabletop. Read the following scene description and extract the physical objects, NPCs, or hazards mentioned.\n"
            "Format the output strictly as a JSON array of objects with 'name' and 'type' (e.g. 'NPC', 'Prop', 'Hazard').\n"
            "If nothing significant is present, output an empty array [].\n\n"
            f"Scene:\n\"{scene_text}\"\n\n"
            "Output ONLY the JSON array:\n["
        )
        output = self._llama(
            prompt,
            max_tokens=150,
            temperature=0.1,
            top_p=0.9,
            stop=["]"],
        )
        
        raw_text = output.get("choices", [{}])[0].get("text", "").strip()
        # Ensure it closes properly
        if not raw_text.endswith("]"):
            raw_text += "]"
            
        return "[" + raw_text

