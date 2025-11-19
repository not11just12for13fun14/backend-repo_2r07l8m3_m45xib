import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Optional motor import with graceful fallback so the API can start even if Mongo driver isn't present
try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore
    MOTOR_AVAILABLE = True
except Exception as e:  # ModuleNotFoundError or other import-time issues
    AsyncIOMotorClient = None  # type: ignore
    AsyncIOMotorDatabase = None  # type: ignore
    MOTOR_AVAILABLE = False
    logger.warning("motor not available; database features will be no-ops: %s", e)

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "appdb")

_client: Optional["AsyncIOMotorClient"] = None
_db: Optional["AsyncIOMotorDatabase"] = None

async def get_db():
    """Get MongoDB database handle or raise if motor unavailable."""
    if not MOTOR_AVAILABLE:
        raise RuntimeError("MongoDB driver (motor) not available")
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(DATABASE_URL)
        _db = _client[DATABASE_NAME]
    return _db

async def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not MOTOR_AVAILABLE:
        # Graceful no-op to avoid crashing the whole API
        now = datetime.utcnow().isoformat()
        return {**data, "id": "local", "created_at": now, "updated_at": now, "_warning": "motor-missing"}
    db = await get_db()
    now = datetime.utcnow()
    data_with_meta = {**data, "created_at": now, "updated_at": now}
    result = await db[collection_name].insert_one(data_with_meta)
    inserted = await db[collection_name].find_one({"_id": result.inserted_id})
    if inserted and "_id" in inserted:
        inserted["id"] = str(inserted.pop("_id"))
    return inserted or {}

async def get_documents(collection_name: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 50) -> List[Dict[str, Any]]:
    if not MOTOR_AVAILABLE:
        return []
    db = await get_db()
    cursor = db[collection_name].find(filter_dict or {}).limit(limit)
    items: List[Dict[str, Any]] = []
    async for doc in cursor:
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return items
