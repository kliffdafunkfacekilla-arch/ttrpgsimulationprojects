# systems/spatial_chaos.py
import networkx as nx

def compute_chaos_spiral(G: nx.Graph, prison_node_ids: list, center_node_id: int) -> dict:
    """
    Called ONCE during world generation, not every tick.
    Calculates graph distance from each prison to the center,
    then assigns a chaos modifier to every node along those paths.
    Returns a dict: { node_id: chaos_modifier_float }
    """
    modifiers = {}
    for prison_id in prison_node_ids:
        try:
            path = nx.shortest_path(G, source=prison_id, target=center_node_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue  # Prison is on a disconnected island, skip
            
        path_length = len(path)
        for i, node_id in enumerate(path):
            # Nodes closer to the center get higher chaos modifier
            # Modifier decays with distance from center
            distance_from_center = path_length - i
            modifier = max(0.0, 1.0 - (distance_from_center / max(1, path_length)) * 0.7)
            # Take the maximum modifier if multiple prison paths cross this node
            modifiers[node_id] = max(modifiers.get(node_id, 0.0), modifier)
            
    return modifiers

def apply_chaos_spiral_to_database(modifiers: dict):
    """Writes the precomputed modifiers to the cells table once in SQLite."""
    from database import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Map to format: (chaos_base_modifier, id)
    updates = [(mod, node_id) for node_id, mod in modifiers.items()]
    
    cur.executemany(
        'UPDATE cells SET chaos_base_modifier = ? WHERE id = ?',
        updates
    )
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Applied chaos spiral to {len(modifiers)} cells in the database.")
