from pydantic import BaseModel, Field
from typing import Optional, List

class Streak(BaseModel):
    date: str
    minutes: int = 0

class Achievement(BaseModel):
    key: str
    title: str
    unlocked_at: Optional[str] = None

class Session(BaseModel):
    country: str
    duration_minutes: int
    started_at: str
    landed_at: Optional[str] = None

class User(BaseModel):
    name: str = Field(default="Pilot")
    timezone: Optional[str] = None
    streak_days: int = 0
    achievements: List[Achievement] = []
