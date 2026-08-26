"""
TEDexplore MCP Server
Esponde i dati TEDx (MongoDB Atlas) come tool utilizzabili da un assistente AI.
Homework 3 - AWS Lambda / MCP - unibg_tedx_2026
"""

import os
import logging

from mcp.server.fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient

# ============================================================
# CONFIG
# ============================================================

# La connection string NON va scritta qui: si legge dalla variabile
# d'ambiente MONGO_URI (la stessa usata dalle Lambda), così non finisce
# mai committata su GitHub per errore.
MONGO_URI = os.environ["MONGO_URI"]

DATABASE_NAME = "unibg_tedx_2026"

VIDEOS_COLLECTION = "tedx_videos"
WATCH_NEXT_COLLECTION = "tedx_watch_next"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tedexplore-mcp")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

# ============================================================
# MCP SERVER
# ============================================================

# Niente SSL/certificati: per il test in locale è più semplice girare
# in HTTP puro su localhost. Se in futuro serve esporlo pubblicamente,
# si può riattivare la parte transport_security + certificati.
mcp = FastMCP(
    "tedexplore-server",
    host="127.0.0.1",
    port=8443,
)


# ============================================================
# TOOLS
# ============================================================

@mcp.tool()
async def get_watch_next(talk_id: str, limit: int = 5) -> list[dict]:
    """
    Restituisce i talk TEDx consigliati dopo aver visto talk_id, con
    punteggio e motivazione del suggerimento (related_video / common_tags).
    Usa gli stessi dati pre-calcolati dal job Glue di TEDexplore.
    """

    doc = await db[WATCH_NEXT_COLLECTION].find_one(
        {"_id": str(talk_id)},
        {"_id": 0, "recommendations": 1}
    )

    if not doc:
        return []

    recommendations = doc.get("recommendations", [])[:limit]

    recommended_ids = [
        str(r.get("video_id"))
        for r in recommendations
        if r.get("video_id") is not None
    ]

    videos_cursor = db[VIDEOS_COLLECTION].find(
        {"video_id": {"$in": recommended_ids}},
        {"_id": 0}
    )
    videos = await videos_cursor.to_list(length=len(recommended_ids))
    videos_by_id = {str(v.get("video_id")): v for v in videos}

    result = []
    for rec in recommendations:
        video_id = str(rec.get("video_id"))
        video = videos_by_id.get(video_id)
        if video is None:
            continue
        result.append({
            **video,
            "score": rec.get("score", 0),
            "reasons": rec.get("reasons", []),
        })

    return result


@mcp.tool()
async def search_by_tag(tag: str, limit: int = 5) -> list[dict]:
    """Cerca talk TEDx che hanno un certo tag (es. 'technology', 'education')."""
    cursor = db[VIDEOS_COLLECTION].find(
        {"tags": tag.lower()},
        {"_id": 0, "video_id": 1, "title": 1, "speakers": 1, "url": 1, "tags": 1},
    ).limit(limit)
    return await cursor.to_list(length=limit)


@mcp.tool()
async def search_by_speaker(speaker: str, limit: int = 5) -> list[dict]:
    """Cerca talk TEDx per nome dello speaker (match parziale, case-insensitive)."""
    cursor = db[VIDEOS_COLLECTION].find(
        {"speakers": {"$regex": speaker, "$options": "i"}},
        {"_id": 0, "video_id": 1, "title": 1, "speakers": 1, "url": 1},
    ).limit(limit)
    return await cursor.to_list(length=limit)


@mcp.tool()
async def get_talk(video_id: str) -> dict:
    """Restituisce i dettagli completi di un talk dato il suo video_id."""
    talk = await db[VIDEOS_COLLECTION].find_one(
        {"video_id": str(video_id)},
        {"_id": 0}
    )
    return talk or {"error": f"Nessun talk trovato con video_id '{video_id}'"}


# ============================================================
# RESOURCES
# ============================================================

@mcp.resource("tedexplore://schema")
async def get_schema() -> str:
    """Espone lo schema delle collezioni TEDexplore come risorsa."""
    return """
    Collection: tedx_videos
      - video_id: string
      - slug: string
      - speakers: string
      - title: string
      - url: string
      - tags: array[string]

    Collection: tedx_watch_next
      - _id: string          (video_id del talk sorgente)
      - recommendations: array
          - video_id: string
          - score: number
          - reasons: array[string]  ("related_video", "common_tags")
    """


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    logger.info("Avvio TEDexplore MCP server su http://127.0.0.1:8443/mcp")
    mcp.run(transport="streamable-http")