# 🌍 Omnis World Engine

The Omnis World Engine is a massive, procedural living-world simulation backend designed to hook into Azgaar's Fantasy Map Generator. It turns a static map into a breathing world where factions rise and fall, ecologies mutate, crime syndicates form, and deep character traits drive global doctrines.

## 🚀 How the Simulation Runs

The Omnis Engine operates as a local Python backend that is **driven entirely by Azgaar's frontend**. 

- You do **not** need to manually run tick loops via console commands.
- The `omnis_bridge.js` injected into Azgaar automatically sends map data (cells, routes, burgs) and tick progression commands to `server.py` via an API.

**To Start the Backend Engine:**
Open a terminal and run the FastApi bridge:
```bash
python server.py
```

## 🧩 Core Architecture & File Structure

The engine is modular, separating different systems into distinct Python files under the `modules/` directory.

- `server.py`: The FastAPI bridge. Receives map data and tick commands from Azgaar and sends back updated simulation states.
- `manage_data.py`: Handles state management, data ingestion, and database operations.
- `omnis_bridge.js` (in frontend): Injects into Azgaar to send cell data, routes, and burgs to `server.py`.
- **`modules/`**
  - **`rules_engine.py`**: The heart of the simulation. Calculates population growth, well-being, crime, resource refining, and overarching Faction Doctrines.
  - **`ecology_system.py`**: Simulates the biological world. Tracks the populations of fauna and flora, handling predation, starvation, and domestication.
  - **`tag_system.py`**: The universal interaction handler. It manages physical and logical interactions across the entire simulation with minimal code (e.g., anything tagged `[Fire]` will interact with and destroy anything tagged `[Flammable]`).
  - **`fringe_system.py`**: Specifically handles Non-Faction independent entities such as the Obsidian Cartel, smuggling rings, pirate fleets, and independent trading empires.
  - **`simulation_lore.py`**: Houses the lore-specific mechanics such as the Chaos Effects, Wardens, Cults, and the Magistar Prisons.
  - **`expansion_system.py` & `diplomacy_system.py`**: Handles how factions claim new territory, build watchtowers, and interact with neighbors.

## 🧠 The Paragon & Doctrine System

The simulation does not rely purely on random math. Instead, the decisions a faction makes are driven by its **Leadership (Paragons)** and the resulting **Faction Doctrines**.

### Paragon Generation
Every faction generates leaders (Supreme Leaders, Mayors, Guard Captains) using a strict Trait system:
- **1 Blessing** (e.g. `Diplomat`, `War Survivor`, `Valiant`)
- **1 Curse** (e.g. `Corrupt`, `Cruel`, `Paranoid`)
- **3 Neutrals** (e.g. `Stoic`, `Pragmatist`, `Ambitious`)
- **Mutations:** There is a 1% chance for any neutral trait to mutate into an extreme blessing or curse.

These traits dynamically warp the leader's **12 Base Stats** (Might, Finesse, Charm, Logic, etc.).

### Faction Doctrines
At the start of every tick, the engine calculates the Faction's Doctrines by combining the Faction's current state (Starvation, Crime) with the Paragon's Stats.

1. **Civil Stance** (Oppressive, Authoritarian, Neutral, Liberal, Utopian)
   - *Effect:* Dictates how the faction handles Crime vs Discontent. (e.g., Utopias have zero discontent but high crime; Oppressive states crush crime but spark riots).
2. **Economical Stance** (Scavenger, Subsistence, Balanced, Industrialist, Wealth-Focused)
   - *Effect:* Drives crafting priorities. Wealth-Focused factions hoard luxuries, spawning crime syndicates due to the wealth gap. Scavengers ignore infrastructure to desperately farm food.
3. **Political Stance** (Isolationist, Defensive, Neutral, Expansionist, Aggressive)
   - *Effect:* Determines construction. Aggressive factions prioritize Barracks over Farms. Defensive factions prioritize Walls.

## ⚖️ Crime, Riots, and the Syndicate

The simulation features a deep social-economic loop:
- **Discontent & Crime:** Starvation, poor weather, and lack of luxury goods raise Discontent. High Discontent leads to Crime.
- **The Obsidian Cartel (Fringe System):** If Crime spirals out of control, criminal syndicates construct illicit structures (Gambling Dens, Black Markets). 
- **Narcotics Spiral:** Syndicates will harvest `Ghost Flowers` and `Night-Nectar` to brew **Narcotics**. Narcotics provide a massive boost to happiness, but inflict a devastating **50% penalty to all production efficiency**, leading to a death spiral of starvation and addiction.
- **Riots:** High Discontent and Crime trigger Riots. Local Paragons resolve Riots based on their traits (e.g., a "Cruel" leader will violently suppress the riot, causing civilian casualties, while a "Diplomat" will drain food reserves to negotiate peace).

## ⚡ Elements, Magic, and Chaos

The simulation operates under deep fantasy lore:
- **12 Elements:** Factions mine standard ores (Iron, Copper) but also seek rare aetheric elements (Lithium, Tungsten, Titanium, Phosphorus, etc.).
- **Magistar Prisons:** 12 massive prisons seal away ancient beings. As prisons weaken, the region's **Chaos Level** rises.
- **Reality Storms:** High chaos spawns anomalous weather that mutates fauna, decays buildings, and transmutes resources.
- **Sparkborn Magic:** 50% of the population possesses a magical affinity for one of the 12 powers (Sensitive -> Epic). Highly advanced magic users, such as Paragons, may wield multiple powers at once.

## 🧹 Maintenance

- **Backups:** The engine automatically creates a backup of the python files in the `backups/latest/` directory before major changes are made.
- **Save State:** Simulation state is saved continuously into a local database/JSON store. Restarting the script resumes from the last tick.
