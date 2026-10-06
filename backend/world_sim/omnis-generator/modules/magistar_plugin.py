# magistar_plugin.py

MAGISTAR_PHYSICS = {
    "Tiraton": {"gravity_mult": 10.0, "structural_integrity": 0.5},
    "Stagus": {"temp_offset": -50.0, "stasis_rate": 0.8},
    "Metrion": {"logic_decay": 2.0, "tech_failure_rate": 0.4}
}

def calculate_reality_spike(magistar_id, active_status):
    """Overrides local physics based on Magistar presence."""
    if not active_status:
        return {"gravity_mult": 1.0, "structural_integrity": 1.0}

    # Apply the specific Magistar domain physics
    return MAGISTAR_PHYSICS.get(magistar_id, {"gravity_mult": 1.0, "integrity": 1.0})
