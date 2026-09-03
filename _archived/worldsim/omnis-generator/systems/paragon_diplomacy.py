# systems/paragon_diplomacy.py

def run_paragon_pass(model, tick: int):
    """
    Called from WorldModel.step() after stage_economy but before stage_diplomacy.
    Reads all paragons once, and applies their traits to the relevant agents.
    Uses type name checks to avoid circular imports with simulation_engine.
    """
    from database import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM paragons')
        paragons = [dict(row) for row in cur.fetchall()]
    except Exception:
        # Table might be empty or missing in early phases
        paragons = []
    cur.close()
    conn.close()
    
    for paragon in paragons:
        cell_id = paragon['macro_group_id']
        # Find the FactionAgent on this cell
        occupants = model.grid.get_cell_list_contents([cell_id])
        faction = next((a for a in occupants if type(a).__name__ == 'FactionAgent'
                        and a.cell_id == cell_id), None)
        if faction is None:
            continue
            
        # Apply economic bonus
        if paragon['economic_trait'] > 0.5:
            cell = next((a for a in occupants if type(a).__name__ == 'CellAgent'), None)
            if cell:
                cell.food_supply = min(1.0, cell.food_supply * 1.2)  # +20% yield
                cell._changed = True
                
        # Apply chaos corruption
        if paragon['chaos_corruption'] > 0.7:
            faction.discontent = min(1.0, faction.discontent + 0.05)
            faction.chaos_level = min(1.0, faction.chaos_level + 0.03)
            faction._changed = True
            
            # Spread to neighbors
            for npos in list(model.G.neighbors(cell_id)):
                neighbor_occupants = model.grid.get_cell_list_contents([npos])
                for a in neighbor_occupants:
                    if type(a).__name__ == 'CellAgent':
                        a.chaos_saturation = min(1.0, a.chaos_saturation + 0.02)
                        a._changed = True
