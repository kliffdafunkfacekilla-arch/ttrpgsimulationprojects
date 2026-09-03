from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base

class HexState(Base):
    """
    SQLAlchemy Model representing the state of a single macro-grid hex.
    This serves as the primary data storage layer for the 4-tier simulation hierarchy,
    nesting high-granularity tactical and local entities inside performance-optimized JSONB columns.
    """
    __tablename__ = "hex_states"

    # =========================================================================
    # Level 4 & 3: Global / Regional (SQL Columns for indexing and fast querying)
    # =========================================================================
    
    # Unique identifier of the hex coordinate/grid cell (Primary Key)
    hex_id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Current engine simulation tick count for this hex state
    tick_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Physical/Geographical properties
    elevation: Mapped[float] = mapped_column(Float, nullable=False)
    moisture: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Sociopolitical & supernatural regional markers
    faction_id: Mapped[str | None] = mapped_column(String, nullable=True)
    macro_stability: Mapped[float] = mapped_column(Float, nullable=False)
    aetheric_leak_rate: Mapped[float] = mapped_column(Float, nullable=False)
    
    # NEW Layer 3 JSONB columns for espionage and warfare simulation tracking
    military_engagements: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    covert_networks: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)

    # =========================================================================
    # Level 2.5: Permanent environmental scars / damage
    # =========================================================================
    local_scars: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)

    # =========================================================================
    # Level 2: Local / Urban (Nested JSONB)
    # =========================================================================
    
    # Local city metric thresholds: keys like 'happy_meter', 'crime_rating', 'arts_score'
    urban_meters: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    
    # Settlement stockpiles: raw materials (e.g. 'timber', 'grain') and refined goods (e.g. 'steel')
    stockpiles: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    
    # Population counts by fantasy species group: e.g. {"Bears": 150, "Mice": 300}
    demographics: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)

    # =========================================================================
    # Level 1: Ground Tactical (Nested JSONB Array)
    # =========================================================================
    
    # List of individual character and wildlife objects, tracking traits, fears, hunger, sanity, and actions
    local_entities: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)

    def __repr__(self) -> str:
        return (
            f"<HexState(hex_id='{self.hex_id}', tick_count={self.tick_count}, "
            f"faction_id='{self.faction_id}', stability={self.macro_stability})>"
        )


class WorldSettings(Base):
    """
    SQLAlchemy Model representing the simulation configuration variables.
    Allows real-time narrative shaping by dynamically tuning metabolisms, flow rates, and crops.
    """
    __tablename__ = "world_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    global_magic_flow: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0", nullable=False)
    global_metabolism_rate: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0", nullable=False)
    base_crop_yield: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0", nullable=False)
    
    # Specific overrides dictionaries
    species_modifiers: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
    faction_modifiers: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}", nullable=False)

    def __repr__(self) -> str:
        return f"<WorldSettings(magic={self.global_magic_flow}, metabolism={self.global_metabolism_rate}, crops={self.base_crop_yield})>"


class EventLog(Base):
    """
    SQLAlchemy Model representing simulation state narrative logs for strategic events.
    Used for story generation and historical reconstruction in TTRPG worldbuilding.
    """
    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tick_count: Mapped[int] = mapped_column(Integer, nullable=False)
    hex_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False) # e.g. "SIEGE", "FAMINE", "STORM", "REBELLION"
    severity: Mapped[int] = mapped_column(Integer, nullable=False) # Severity 1-5
    summary: Mapped[str] = mapped_column(String, nullable=False) # A one-sentence description
    
    # Nullable deep snapshot for high-detail tracking
    deep_snapshot: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    
    # List of hero IDs/names witnessing this event
    witnessed_by_heroes: Mapped[list | None] = mapped_column(JSONB, default=list, server_default="'[]'::jsonb", nullable=True)

    def __repr__(self) -> str:
        return f"<EventLog(type='{self.event_type}', tick={self.tick_count}, hex='{self.hex_id}', severity={self.severity})>"
