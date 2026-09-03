from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class CampaignState(Base):
    __tablename__ = "campaign_states"

    id = Column(String, primary_key=True, index=True)
    player_id = Column(String, index=True)
    current_hex = Column(Integer, default=1)
    
    # 4-Layer Hierarchy Positions
    current_layer = Column(Integer, default=1)
    current_region_x = Column(Integer, default=10)
    current_region_y = Column(Integer, default=10)
    current_local_x = Column(Integer, default=50)
    current_local_y = Column(Integer, default=50)
    current_player_x = Column(Integer, default=50)
    current_player_y = Column(Integer, default=50)

    tension = Column(Integer, default=10)
    weather = Column(String, default="Clear Skies")
    chaos_numbers = Column(JSON, default="[1]")
    
    pacing_current = Column(Integer, default=0)
    pacing_goal = Column(Integer, default=15)
    
    player_sprite = Column(JSON, nullable=True)
    difficulty = Column(String, default="STANDARD")
    style = Column(String, default="GRITTY_SURVIVAL")
    length_type = Column(String, default="SAGA")
    no_fly_list = Column(JSON, default="[]")
    
    hex_densities = Column(JSON, default="{}")
    active_encounter = Column(JSON, nullable=True)
    
    # World Clock
    current_time = Column(Float, default=9.0) # 0.0 to 24.0
    day_phase = Column(String, default="MORNING")
    
    # NPC state tracking (JSON blob for now)
    npc_states = Column(JSON, default="{}")

class NPCEntity(Base):
    __tablename__ = "npc_entities"
    id = Column(String, primary_key=True)
    campaign_id = Column(String, index=True)
    name = Column(String)
    hex_id = Column(Integer, index=True)
    lx = Column(Integer, default=50)
    ly = Column(Integer, default=50)
    hp = Column(Integer, default=10)
    max_hp = Column(Integer, default=10)
    disposition = Column(String, default="NEUTRAL")
    schedule_id = Column(String, nullable=True)

class NPCSchedule(Base):
    __tablename__ = "npc_schedules"
    id = Column(String, primary_key=True)
    name = Column(String)
    # Routines list: [{start: 6.0, end: 9.0, lx: 40, ly: 40, action: "Sleeping"}]
    routines = Column(JSON, default="[]")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, index=True)
    role = Column(String) # "player" or "narrator"
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ActiveQuest(Base):
    __tablename__ = "active_quests"
    id = Column(String, primary_key=True)
    campaign_id = Column(String, index=True)
    title = Column(String)
    objectives = Column(JSON) # List of {objective: str, is_complete: bool}

class CampaignFrameworkTable(Base):
    __tablename__ = "campaign_frameworks"
    campaign_id = Column(String, primary_key=True)
    arc_name = Column(String)
    theme = Column(String)
    hero_journey = Column(JSON)
    character_hooks = Column(JSON)

class WorldEventsLog(Base):
    __tablename__ = "world_events_log"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, index=True)
    turn_number = Column(Integer)
    event_description = Column(String)
    associated_faction = Column(String, nullable=True)
    location_hex_id = Column(String)

class WorldDelta(Base):
    __tablename__ = "world_deltas"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, index=True)
    hex_id = Column(Integer, index=True)
    layer = Column(Integer) # 2 (Region), 3 (Local), 4/5 (Tactical)
    x = Column(Integer)
    y = Column(Integer)
    original_value = Column(String)
    new_value = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
