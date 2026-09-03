import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:latest"

def _call_ollama(prompt, model=MODEL_NAME):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        response.raise_for_status()
        output = response.json().get("response", "{}")
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            if "```json" in output:
                clean = output.split("```json")[1].split("```")[0].strip()
                return json.loads(clean)
            return {"narrative": "Failed to parse JSON: " + output}
    except Exception as e:
        return {"narrative": f"Error contacting Ollama: {str(e)}"}


def generate_campaign_intro(characters, world_context, model=MODEL_NAME):
    prompt = f"""You are the AI Game Master.
Two players have created the following characters:
{json.dumps(characters, indent=2)}

Here is the world context and their starting location:
{world_context}

Your task:
1. Formulate an overarching "story_framework" (the main plot hook).
2. Generate a "narrative" introduction setting the scene at the starting location, introducing the characters into the world.
3. If they meet anyone immediately, define them in "new_npcs".

Return STRICT JSON:
{{
    "story_framework": "A mysterious plague is sweeping the shatterlands...",
    "narrative": "The tavern in Ostraka is loud tonight...",
    "new_npcs": [{{ "name": "Barkeep Bob", "personality": "Grizzled and tired" }}]
}}
"""
    return _call_ollama(prompt, model)


def process_player_action(world_context, campaign_state, player_action, model=MODEL_NAME):
    prompt = f"""You are the AI Game Master.
World Context: {world_context}
Campaign State: {campaign_state}

The players take the following action: "{player_action}"

Determine the outcome. If the action is difficult or risky (e.g., attacking, lying, lifting something heavy, dodging), require a skill check by returning the "skill_check" object.
Valid stats for skill checks are: brawn, reflexes, wit, presence.

Return STRICT JSON with up to 4 keys:
1. "narrative": Describe the immediate result (or the setup if a skill check is required).
2. "state_shifts": (Optional) Database changes.
3. "skill_check": (Optional) Include if a dice roll is needed. Format: {{"stat": "brawn", "dc": 12, "reasoning": "Trying to smash the door"}}
4. "new_npcs": (Optional) List of new NPCs encountered: [{{"name": "...", "personality": "..."}}]

Example:
{{
    "narrative": "You lunge at the goblin! Let's see if you can hit it.",
    "skill_check": {{"stat": "reflexes", "dc": 10, "reasoning": "Striking a nimble foe"}},
    "new_npcs": []
}}
"""
    return _call_ollama(prompt, model)


def resolve_skill_check(world_context, player_action, skill_check_data, stat_val, roll, total, model=MODEL_NAME):
    success = total >= skill_check_data.get("dc", 10)
    prompt = f"""You are the AI Game Master.
The players attempted: "{player_action}"
You required a skill check for: {skill_check_data.get('reasoning')} (DC {skill_check_data.get('dc', 10)})
The player rolled a total of {total} (Die roll + Stat modifier of {stat_val}).
Result: {'SUCCESS' if success else 'FAILURE'}.

Describe the outcome of this action based on the roll.
Return STRICT JSON:
{{
    "narrative": "With a mighty swing, you cleave the goblin in two!",
    "state_shifts": {{}}
}}
"""
    return _call_ollama(prompt, model)
