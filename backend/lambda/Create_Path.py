import os
import re
import json
import logging
from collections import defaultdict
from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URI"]
DB_NAME = "unibg_tedx_2026"
MIN_VIDEOS = 3
MAX_PATHS = 30
MIN_TAG_LENGTH = 3

logging.getLogger().setLevel(logging.INFO)

def norm(value):
    return re.sub(r"\s+", " ", str(value).lower()).strip() if value else ""


def path_id(prefix, value):
    value = re.sub(r"[^a-z0-9_-]", "", norm(value).replace(" ", "_"))
    return f"{prefix}_{value}"


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a and b else 0


def add_path(paths, prefix, title, videos, kind):
    if len(videos) >= MIN_VIDEOS:
        paths.append({
            "path_id": path_id(prefix, title),
            "title": title,
            "type": kind,
            "videos": sorted(videos),
            "video_count": len(videos)
        })

def lambda_handler(event, context):

    client = None

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]

        videos = list(db["tedx_videos"].find(
            {},
            {
                "_id": 1,
                "video_id": 1,
                "title": 1,
                "speakers": 1,
                "presenterDisplayName": 1,
                "tags": 1
            }
        ))

        if not videos:
            return response(404, {"error": "No videos found"})

        speaker_map = defaultdict(set)
        topic_map = defaultdict(set)

        for video in videos:
            vid = str(video.get("video_id") or video.get("_id") or "")
            if not vid:
                continue

            # Speaker
            speakers = video.get("speakers", [])
            if not isinstance(speakers, list):
                speakers = [speakers] if speakers else []

            presenter = video.get("presenterDisplayName")
            if presenter:
                speakers.append(presenter)

            for speaker in speakers:
                speaker = str(speaker).strip()
                if speaker:
                    speaker_map[speaker].add(vid)

            # Topic / tag
            tags = video.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    tag = str(tag).strip() if tag else ""
                    if len(tag) >= MIN_TAG_LENGTH:
                        topic_map[tag].add(vid)

        # Speaker paths
        speaker_paths = []
        for speaker, vids in speaker_map.items():
            add_path(
                speaker_paths,
                "speaker",
                speaker,
                vids,
                "speaker"
            )

        speaker_paths.sort(
            key=lambda p: p["video_count"],
            reverse=True
        )
        speaker_paths = speaker_paths[:MAX_PATHS]

        # Topic paths
        topic_paths = []
        for topic, vids in topic_map.items():
            add_path(
                topic_paths,
                "topic",
                topic,
                vids,
                "topic"
            )

        topic_paths.sort(
            key=lambda p: p["video_count"],
            reverse=True
        )
        topic_paths = topic_paths[:MAX_PATHS]

        # Remove highly similar topic paths
        final_topic_paths = []

        for path in topic_paths:
            if not any(
                jaccard(path["videos"], other["videos"]) >= 0.80
                for other in final_topic_paths
            ):
                final_topic_paths.append(path)

        final_paths = speaker_paths + final_topic_paths

        paths = db["tedx_paths"]
        paths.delete_many({})

        if final_paths:
            paths.insert_many(final_paths)

        return response(200, {
            "speaker_paths": len(speaker_paths),
            "topic_paths": len(final_topic_paths),
            "total_paths": len(final_paths),
            "videos_analyzed": len(videos)
        })

    except Exception as e:
        logging.exception("Error creating paths")
        return response(500, {"error": str(e)})

    finally:
        if client:
            client.close()

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }