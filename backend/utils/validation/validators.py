"""
Data validation utilities for SAGA Unified.
Provides validation functions for game data and user input.
"""
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ValidationError

def validate_model(model: BaseModel, data: Dict[str, Any]) -> Tuple[bool, Optional[BaseModel], Optional[str]]:
    """
    Validate data against a Pydantic model.

    Args:
        model: Pydantic model class
        data: Dictionary data to validate

    Returns:
        Tuple of (is_valid, validated_instance, error_message)
    """
    try:
        instance = model(**data)
        return True, instance, None
    except ValidationError as e:
        error_msg = f"Validation error: {str(e)}"
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        return False, None, error_msg

def validate_stat_range(stat_name: str, value: int, min_val: int = 1, max_val: int = 20) -> Tuple[bool, Optional[str]]:
    """
    Validate that a stat value is within acceptable range.

    Args:
        stat_name: Name of the stat being validated
        value: Stat value to validate
        min_val: Minimum acceptable value (default: 1)
        max_val: Maximum acceptable value (default: 20)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, int):
        return False, f"{stat_name} must be an integer"

    if value < min_val or value > max_val:
        return False, f"{stat_name} must be between {min_val} and {max_val}"

    return True, None

def validate_character_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate character name for appropriateness and length.

    Args:
        name: Character name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Character name cannot be empty"

    if len(name) > 50:
        return False, "Character name cannot exceed 50 characters"

    if len(name.strip()) < 2:
        return False, "Character name must be at least 2 characters"

    # Check for appropriate characters (alphanumeric, spaces, hyphens, apostrophes)
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -'")
    if not all(c in allowed_chars for c in name):
        return False, "Character name contains invalid characters"

    return True, None

def validate_slot_count(selected_offense: int, selected_defense: int, selected_power: int) -> Tuple[bool, Optional[str]]:
    """
    Validate skill track selection follows B.R.U.T.A.L. rules (1 offense, 1 defense, 2 power).

    Args:
        selected_offense: Number of offense tracks selected
        selected_defense: Number of defense tracks selected
        selected_power: Number of power/utility tracks selected

    Returns:
        Tuple of (is_valid, error_message)
    """
    if selected_offense != 1:
        return False, f"Must select exactly 1 offense track (selected: {selected_offense})"

    if selected_defense != 1:
        return False, f"Must select exactly 1 defense track (selected: {selected_defense})"

    if selected_power != 2:
        return False, f"Must select exactly 2 power/utility tracks (selected: {selected_power})"

    return True, None

def validate_action_economy(move_beats: int, stamina_beats: int, focus_beats: int, max_beats: int = 3) -> Tuple[bool, Optional[str]]:
    """
    Validate action economy costs don't exceed available beats.

    Args:
        move_beats: Move beats required
        stamina_beats: Stamina beats required
        focus_beats: Focus beats required
        max_beats: Maximum beats available (default: 3)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if move_beats < 0 or stamina_beats < 0 or focus_beats < 0:
        return False, "Beat costs cannot be negative"

    if move_beats > max_beats:
        return False, f"Move beats ({move_beats}) exceed maximum ({max_beats})"

    if stamina_beats > max_beats:
        return False, f"Stamina beats ({stamina_beats}) exceed maximum ({max_beats})"

    if focus_beats > max_beats:
        return False, f"Focus beats ({focus_beats}) exceed maximum ({max_beats})"

    return True, None