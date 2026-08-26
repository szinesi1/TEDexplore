import os
import json
import logging

from pymongo import MongoClient


# ============================================================
# CONFIG
# ============================================================

MONGO_URI = os.environ["MONGO_URI"]

DATABASE_NAME = "unibg_tedx_2026"

WATCH_NEXT_COLLECTION = "tedx_watch_next"
VIDEOS_COLLECTION = "tedx_videos"


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ============================================================
# MAIN
# ============================================================

def lambda_handler(event, context):

    client = None

    try:

        # ----------------------------------------------------
        # READ INPUT
        # ----------------------------------------------------

        body = event.get("body")

        if isinstance(body, str):
            body = json.loads(body)

        elif body is None:
            body = event

        talk_id = body.get("talkId")

        if not talk_id:
            return response(
                400,
                {
                    "error": "talkId is required"
                }
            )

        logger.info(
            f"Getting watch-next recommendations for talk {talk_id}"
        )


        # ----------------------------------------------------
        # CONNECT TO MONGODB
        # ----------------------------------------------------

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        db = client[DATABASE_NAME]

        watch_next_collection = db[WATCH_NEXT_COLLECTION]
        videos_collection = db[VIDEOS_COLLECTION]


        # ----------------------------------------------------
        # FIND PRE-COMPUTED RECOMMENDATIONS
        # ----------------------------------------------------

        recommendation_document = (
            watch_next_collection.find_one(
                {
                    "_id": str(talk_id)
                },
                {
                    "_id": 0,
                    "recommendations": 1
                }
            )
        )


        # ----------------------------------------------------
        # NO RECOMMENDATIONS
        # ----------------------------------------------------

        if not recommendation_document:

            return response(
                200,
                {
                    "talkId": talk_id,
                    "total": 0,
                    "recommendations": [],
                    "message": "No recommendations found"
                }
            )


        recommendations = (
            recommendation_document.get(
                "recommendations",
                []
            )
        )


        if not recommendations:

            return response(
                200,
                {
                    "talkId": talk_id,
                    "total": 0,
                    "recommendations": []
                }
            )


        # ----------------------------------------------------
        # GET RECOMMENDED VIDEO IDS
        # ----------------------------------------------------

        recommended_ids = []

        for recommendation in recommendations:

            video_id = recommendation.get("video_id")

            if video_id is not None:
                recommended_ids.append(str(video_id))


        # ----------------------------------------------------
        # GET VIDEO DETAILS
        # ----------------------------------------------------

        videos = list(
            videos_collection.find(
                {
                    "video_id": {
                        "$in": recommended_ids
                    }
                },
                {
                    "_id": 0
                }
            )
        )


        # ----------------------------------------------------
        # CREATE FAST LOOKUP
        # ----------------------------------------------------

        videos_by_id = {
            str(video.get("video_id")): video
            for video in videos
        }


        # ----------------------------------------------------
        # BUILD FINAL RESPONSE
        # ----------------------------------------------------

        result = []


        for recommendation in recommendations:

            video_id = str(
                recommendation.get("video_id")
            )

            video = videos_by_id.get(video_id)

            if video is None:
                continue


            result.append(
                {
                    "video_id": video_id,

                    "score": recommendation.get(
                        "score",
                        0
                    ),

                    "reasons": recommendation.get(
                        "reasons",
                        []
                    ),

                    "video": video
                }
            )


        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return response(
            200,
            {
                "talkId": str(talk_id),
                "total": len(result),
                "recommendations": result
            }
        )


    except Exception as e:

        logger.exception(
            "Error while retrieving watch-next recommendations"
        )

        return response(
            500,
            {
                "error": str(e)
            }
        )


    finally:

        if client is not None:
            client.close()


# ============================================================
# RESPONSE WRAPPER
# ============================================================

def response(status_code, body):

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps(
            body,
            ensure_ascii=False
        )
    }
