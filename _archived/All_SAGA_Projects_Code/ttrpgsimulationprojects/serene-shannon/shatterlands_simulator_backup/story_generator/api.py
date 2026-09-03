# story_generator API – serves narrative data for a 91‑hex cluster

import json
from fastapi import FastAPI, HTTPException, Query
from pathlib import Path

# Local imports – DB utilities we just created
from .db import init_cache_db, sync_region, fetch_region_data, hex_distance

app = FastAPI(title="Shatterlands Narrative Service", version="0.1")

# Simple unpack of packed ecology (same encoding used by the simulator)
def unpack_ecology(pack_ecology: int):
    # Bits layout (based on simulator code):
    #   p1: bits 24‑31, p2: bits 16‑23, p3: bits 8‑15, res: bits 0‑7
    p1 = (pack_ecology >> 24) & 0xFF
    p2 = (pack_ecology >> 16) & 0xFF
    p3 = (pack_ecology >> 8) & 0xFF
    res = pack_ecology & 0xFF
    return p1, p2, p3, res

# Narrative templates – can be expanded later
TEMPLATES = {
    "WORLD_END": "The world shattered at tick {tick} when the {cause} occurred.",
    "Chaos": "Chaos surged in {region} at tick {tick}: {detail}",
    "Resources": "A rare {resource} deposit was discovered at ({q}, {r}) on tick {tick}.",
    "Kamikaze": "A heroic sacrifice sealed a prison on tick {tick}, preventing disaster.",
    "Mandate": "Agents of {faction} carried out a mandate in {region} on tick {tick}.",
    "default": "At tick {tick}, an event of type {category} happened: {message}"
}

def render_event(event, tick):
    category, message, q, r = event
    template = TEMPLATES.get(category, TEMPLATES["default"])
    if category == "WORLD_END":
        return template.format(tick=tick, cause=message)
    if category == "Resources":
        # Try to extract resource name from the message (very naive)
        resource = "unknown"
        parts = message.split()
        if "deposit" in parts:
            try:
                idx = parts.index("deposit")
                resource = parts[idx + 2]  # after "of"
            except Exception:
                pass
        return template.format(tick=tick, resource=resource, q=q, r=r)
    if category in ("Chaos", "Kamikaze", "Mandate"):
        return template.format(tick=tick, region=message, detail=message, faction=message)
    return template.format(tick=tick, category=category, message=message)

@app.get("/narrative")
def get_narrative(
    x: int = Query(..., description="Axial q coordinate of the player centre"),
    y: int = Query(..., description="Axial r coordinate of the player centre"),
    radius: int = Query(5, description="Radius of the hex cluster (default 5 → 91 hexes)"),
):
    # Ensure cache DB is ready – the poller normally keeps it up‑to‑date, but we lazily init it here.
    init_cache_db()

    # On‑demand sync for the requested region (lightweight, pulls only needed rows)
    sync_region(x, y, radius)

    events, hexes = fetch_region_data(x, y, radius)

    # Build narrative strings from events
    narratives = []
    for ev in events:
        q, r, tick, category, message = ev
        narratives.append(render_event((category, message, q, r), tick))

    # Build a simple feature list from hex details (e.g., resources, lake, river)
    features = []
    for hx in hexes:
        q, r, pack_ecology, river_volume, is_lake, chaos_seed = hx
        p1, p2, p3, res = unpack_ecology(pack_ecology)
        # Very small description – can be expanded later
        if is_lake:
            features.append(f"Lake at ({q},{r})")
        if river_volume > 0:
            features.append(f"River segment (volume {river_volume}) at ({q},{r})")
        if res != 0:
            features.append(f"Resource type {res} at ({q},{r})")
        if p1 > 200:
            features.append(f"High chaos aura (p1={p1}) at ({q},{r})")

    response = {
        "center": {"q": x, "r": y},
        "radius": radius,
        "hex_count": len(hexes),
        "event_count": len(events),
        "narratives": narratives,
        "features": list(set(features)),  # dedupe
    }
    return response

# Entry‑point for `python -m story_generator.api`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
