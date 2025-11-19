import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import math

# Ensure local modules (e.g., database.py) are importable even if CWD differs
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from database import create_document, get_documents

app = FastAPI(title="Study Air API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic data: country coords (lat, lon)
COUNTRIES: Dict[str, Dict[str, float]] = {
    "United States": {"lat": 38.0, "lon": -97.0, "airport": "JFK"},
    "United Kingdom": {"lat": 51.509, "lon": -0.118},
    "France": {"lat": 48.8566, "lon": 2.3522},
    "Germany": {"lat": 52.52, "lon": 13.405},
    "Japan": {"lat": 35.6895, "lon": 139.6917},
    "Australia": {"lat": -33.8688, "lon": 151.2093},
    "Brazil": {"lat": -23.5505, "lon": -46.6333},
    "South Africa": {"lat": -26.2041, "lon": 28.0473},
    "Canada": {"lat": 45.4215, "lon": -75.6972},
    "Singapore": {"lat": 1.3521, "lon": 103.8198},
}

INDIA = {"lat": 28.6139, "lon": 77.2090}  # New Delhi approx

class FlightRequest(BaseModel):
    country: str
    speed_kmh: float = 900.0  # typical cruising speed

class FlightResponse(BaseModel):
    country: str
    distance_km: float
    duration_minutes: int
    path: List[Dict[str, float]]


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def great_circle_points(start, end, steps=64):
    # simple linear interpolation in lat/lon (approx for animation)
    lat1, lon1 = start["lat"], start["lon"]
    lat2, lon2 = end["lat"], end["lon"]
    pts = []
    for i in range(steps + 1):
        t = i / steps
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t
        pts.append({"lat": lat, "lon": lon})
    return pts


@app.get("/")
async def root():
    return {"message": "Study Air backend running"}


@app.get("/countries")
async def get_countries():
    return {"countries": list(COUNTRIES.keys())}


@app.post("/flight", response_model=FlightResponse)
async def compute_flight(req: FlightRequest):
    country = req.country
    if country not in COUNTRIES:
        return FlightResponse(country=country, distance_km=0, duration_minutes=0, path=[])
    start = INDIA
    dest = COUNTRIES[country]
    d = haversine(start["lat"], start["lon"], dest["lat"], dest["lon"])
    hours = d / req.speed_kmh
    minutes = int(round(hours * 60))
    path = great_circle_points(start, dest)
    return FlightResponse(country=country, distance_km=round(d, 2), duration_minutes=minutes, path=path)


@app.get("/achievements")
async def list_achievements():
    items = await get_documents("achievement")
    return {"items": items}


class AchievementCreate(BaseModel):
    key: str
    title: str


@app.post("/achievements")
async def create_achievement(payload: AchievementCreate):
    doc = await create_document("achievement", payload.model_dump())
    return doc


@app.get("/test")
async def test():
    # database status sample
    return {
        "backend": "Study Air API",
        "database": "MongoDB",
        "database_url": "env:DATABASE_URL",
        "database_name": "env:DATABASE_NAME",
        "connection_status": "ok",
        "collections": ["achievement"],
    }
