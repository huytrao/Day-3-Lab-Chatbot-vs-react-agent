import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)


@lru_cache
def get_settings() -> dict:
    return {
        "mongo_uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        "mongo_db_name": os.getenv("MONGO_DB_NAME", "vinwonders_agent"),
    }


settings = get_settings()
client = AsyncIOMotorClient(settings["mongo_uri"])
db: AsyncIOMotorDatabase = client[settings["mongo_db_name"]]


async def ping_database() -> None:
    await client.admin.command("ping")


def close_database() -> None:
    client.close()
