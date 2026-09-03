# Project Okasha: Master Construction Manual

## Part 1: Database Initialization

1. **Install PostgreSQL.**
2. Open your SQL Query tool.
3. Copy and paste this exact command to build the **World-State Container**:

```sql
CREATE TABLE region_cells (
    cell_id SERIAL PRIMARY KEY,
    x_coord INTEGER,
    y_coord INTEGER,
    name TEXT,
    population INTEGER DEFAULT 100,
    food_supply INTEGER DEFAULT 500,
    morale INTEGER DEFAULT 50,
    chaos_rating FLOAT DEFAULT 0.0,
    lore_link TEXT
);
```

4. Run the command. You should see a "Success" message.

## Part 2: Data Ingestion (The CSV Import)

Your CSV files (like `Okasha Burgs.csv`) are the raw ingredients. You must move them into the `region_cells` table.

1. **Open Python.** Install `pandas` (type `pip install pandas` in your terminal).
2. Create a file named `ingest.py` and paste this to pull your data into the database:

```python
import pandas as pd
from sqlalchemy import create_engine

# Connect to your DB
engine = create_engine('postgresql://username:password@localhost:5432/okasha_world')

# Load your CSV
df = pd.read_csv('Okasha Burgs.csv')

# Push data to your table
df.to_sql('region_cells', engine, if_exists='append', index=False)
```

3. Run `python ingest.py`. Your map data is now "live" in the database.

## Part 3: The Calendar Engine (The "Time" Code)

This logic tracks your seasons, moon wobble, and the annual eclipse. Create a file named `calendar.py`:

```python
def get_world_state(tick):
    # 360-day year
    day_of_year = tick % 360
    
    # Sun Eclipse (last 7 days of year)
    if day_of_year >= 354:
        return "ECLIPSE_MODE"
    
    # Moon Wobble (4 Quadrants)
    quadrant = (tick // 90) % 4 
    return {"quadrant": quadrant, "status": "ACTIVE"}
```

## Part 4: The Simulation Loop (The "Living World")

This is the heart of the project. Create a file named `engine.py`. This script runs once for every "Sim Tick."

1. **Calculate Resources:**
* `population = population`
* `production = population * 0.1` (Labor efficiency)
* `new_food = current_food + production`

2. **Apply Chaos Multiplier:**
* Get `quadrant` from `calendar.py`.
* If `quadrant == 1` (Top-Left): `chaos_rating += 0.5`.

3. **Update Database:**
* Use a SQL `UPDATE` command to set the new food and morale values back into your `region_cells` table.

## Part 5: Connecting the Lore

To make the database "smart," you link the `lore_link` field to your markdown files.

1. In your `region_cells` table, every row has a `lore_link` column.
2. Paste the filename (e.g., `Chapter_01_The_First_Age_v1.6.md`) into that column for the corresponding region.
3. When a player enters a cell, your app queries that file:
* `SELECT lore_link FROM region_cells WHERE cell_id = [PLAYER_LOCATION];`

4. Your front-end reads that specific Markdown file and displays the text.

---

### The Automaton's Golden Rules:

* **DO NOT SKIP STEPS.** If Part 1 fails, the database doesn't exist.
* **USE THE CSV NAMES.** Make sure the column names in your CSVs exactly match the names in your `CREATE TABLE` command, or the Python script will error.
* **THE TICKET IS THE KEY.** The "Tick" is just a number that goes up by 1. Keep a text file named `current_tick.txt` and read/write to it every time your script runs.
