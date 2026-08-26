import os
import json
import logging

from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URI"]
DATABASE_NAME = "unibg_tedx_2026"
PROGRESS_COLLECTION = "tedx_user_progress"
QUIZ_RESULTS_COLLECTION = "tedx_quiz_results"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    client = None

    try:
        # Supporta sia GET (userId in querystring) sia POST (userId nel body)
        query_params = event.get("queryStringParameters") or {}
        user_id = query_params.get("userId")

        if not user_id:
            body = event.get("body")
            if isinstance(body, str):
                body = json.loads(body)
            elif body is None:
                body = event
            user_id = body.get("userId")

        if not user_id:
            return response(400, {"error": "userId is required"})

        logger.info(f"Retrieving learning stats for user: {user_id}")

        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]

        progress_docs = list(db[PROGRESS_COLLECTION].find(
            {"userId": user_id},
            {"_id": 0, "talkId": 1, "progressSeconds": 1, "watched": 1, "completed": 1}
        ))

        # Talk unici per evitare doppi conteggi se ci sono piu' documenti
        # di progresso per lo stesso talk (es. l'utente lo riapre)
        watched_talks = set()
        completed_talks = set()
        total_seconds = 0.0

        for p in progress_docs:
            talk_id = p.get("talkId")

            try:
                total_seconds += float(p.get("progressSeconds", 0) or 0)
            except (TypeError, ValueError):
                pass

            if talk_id is None:
                continue

            if p.get("watched") or p.get("completed"):
                watched_talks.add(str(talk_id))
            if p.get("completed"):
                completed_talks.add(str(talk_id))

        # Quiz: campo "completed" mancante = NON completato (non il contrario)
        quiz_docs = list(db[QUIZ_RESULTS_COLLECTION].find(
            {"userId": user_id},
            {"_id": 0, "quizId": 1, "score": 1, "completed": 1}
        ))

        completed_quizzes = [q for q in quiz_docs if q.get("completed", False)]

        scores = []
        for q in completed_quizzes:
            try:
                scores.append(float(q.get("score")))
            except (TypeError, ValueError):
                continue

        stats = {
            "userId": user_id,
            "talksWatched": len(watched_talks),
            "talksCompleted": len(completed_talks),
            "minutesViewed": round(total_seconds / 60, 1),
            "quizzesCompleted": len(completed_quizzes),
            "averageQuizScore": round(sum(scores) / len(scores), 1) if scores else 0,
        }

        return response(200, stats)

    except Exception as e:
        logger.exception("Error retrieving learning stats")
        return response(500, {"error": "Internal server error", "details": str(e)})

    finally:
        if client is not None:
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
