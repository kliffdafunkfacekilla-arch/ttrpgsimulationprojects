from typing import TypedDict, List, Dict, Any, Optional

class GameState(TypedDict):
    player_id: str
    action_type: str
    action_target: str
    raw_chat_text: str
    stamina_burned: int
    focus_burned: int
    current_location: str
    current_layer: int
    current_region_x: int
    current_region_y: int
    current_local_x: int
    current_local_y: int
    current_player_x: int
    current_player_y: int
    player_vitals: Dict[str, Any]
    player_powers: List[Any]
    active_quests: List[Dict[str, Any]]
    weather: str
    tension: int
    chaos_numbers: List[int]
    math_log: str
    chaos_strike: bool
    chaos_narrative: str
    visual_assets: Dict[str, str]
    director_override: Optional[Dict[str, Any]]
    vtt_commands: List[Dict[str, Any]]
    campaign_framework: List[Dict[str, Any]]
    current_stage: int
    current_stage_progress: int
    active_regional_arcs: List[Dict[str, Any]]
    active_local_quests: List[Dict[str, Any]]
    active_errands: List[Dict[str, Any]]
    ai_narration: str
    chat_history: List[Dict[str, Any]]
    player_sprite: Optional[Dict[str, Any]]
    difficulty: str
    style: str
    length_type: str
    no_fly_list: List[str]
    pacing_goal: int
    active_encounter: Optional[Dict[str, Any]]
