from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PlayerDocument(BaseModel):
    name: str
    overall_rating: int
    age: int
    nationality: str
    league_name: str
    club_name: str
    position: str
    pace: int = 0
    shooting: int = 0
    passing: int = 0
    dribbling: int = 0
    defending: int = 0
    physic: int = 0
    preferred_foot: str = ""
    height: str = ""
    weight: str = ""
    weak_foot: int = 0
    skill_moves: int = 0
    alt_positions: str = ""
    acceleration: int = 0
    sprint_speed: int = 0
    finishing: int = 0
    shot_power: int = 0
    long_shots: int = 0
    vision: int = 0
    crossing: int = 0
    short_passing: int = 0
    long_passing: int = 0
    ball_control: int = 0
    agility: int = 0
    reactions: int = 0
    composure: int = 0
    interceptions: int = 0
    heading: int = 0
    def_awareness: int = 0
    standing_tackle: int = 0
    sliding_tackle: int = 0
    jumping: int = 0
    stamina: int = 0
    strength: int = 0
    aggression: int = 0
    positioning: int = 0
    volleys: int = 0
    penalties: int = 0
    gk_diving: int = 0
    gk_handling: int = 0
    gk_kicking: int = 0
    gk_positioning: int = 0
    gk_reflexes: int = 0
    composite_score: float = 0.0
    value_eur: float = 0.0
    stats_embedding: List[float] = []


class MemoryDocument(BaseModel):
    session_id: str
    memory_type: str
    content: dict
    embedding: List[float] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class ShortlistDocument(BaseModel):
    session_id: str
    name: str
    player_names: List[str]
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentRunDocument(BaseModel):
    session_id: str
    query: str
    agent: str
    plan: list = []
    tool_calls: list = []
    final_output: str = ""
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


def serialize(doc: dict) -> dict:
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc