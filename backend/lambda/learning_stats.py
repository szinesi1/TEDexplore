import os
import json
import logging

from pymongo import MongoClient


# ============================================================
# CONFIG
# ============================================================

MONGO_URI = os.environ["MONGO_URI"]

DATABASE_NAME = "unibg_tedx_2026"

PROGRESS_COLLECTION = "tedx_user_progress"
QUIZ_RESULTS_COLLECTION = "tedx_quiz_results"


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

        user_id = body.get("userId")

        if not user_id:

            return response(
                400,
                {
                    "error": "userId is required"
                }
            )


        logger.info(
            f"Retrieving learning stats for user: {user_id}"
        )


        # ----------------------------------------------------
        # CONNECT TO MONGODB
        # ----------------------------------------------------

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        db = client[DATABASE_NAME]

        progress_collection = db[
            PROGRESS_COLLECTION
        ]

        quiz_collection = db[
            QUIZ_RESULTS_COLLECTION
        ]


        # ====================================================
        # 1. USER VIDEO PROGRESS
        # ====================================================

        progress_documents = list(
            progress_collection.find(
                {
                    "userId": user_id
                },
                {
                    "_id": 0,
                    "talkId": 1,
                    "progressSeconds": 1,
                    "watched": 1,
                    "completed": 1
                }
            )
        )


        # ----------------------------------------------------
        # Number of unique talks watched
        # ----------------------------------------------------

        watched_talks = set()

        talks_completed = 0

        total_seconds = 0


        for progress in progress_documents:

            talk_id = progress.get(
                "talkId"
            )

            if talk_id is not None:

                if (
                    progress.get(
                        "watched",
                        False
                    )
                    or
                    progress.get(
                        "completed",
                        False
                    )
                ):

                    watched_talks.add(
                        str(talk_id)
                    )


            # ------------------------------------------------
            # Viewed time
            # ------------------------------------------------

            progress_seconds = (
                progress.get(
                    "progressSeconds",
                    0
                )
            )


            try:

                progress_seconds = float(
                    progress_seconds
                )

            except (
                TypeError,
                ValueError
            ):

                progress_seconds = 0


            total_seconds += progress_seconds


            # ------------------------------------------------
            # Completed talks
            # ------------------------------------------------

            if progress.get(
                "completed",
                False
            ):

                talks_completed += 1


        # Convert seconds → minutes

        minutes_viewed = round(
            total_seconds / 60,
            1
        )


        # ====================================================
        # 2. QUIZ STATISTICS
        # ====================================================

        quiz_documents = list(
            quiz_collection.find(
                {
                    "userId": user_id
                },
                {
                    "_id": 0,
                    "quizId": 1,
                    "score": 1,
                    "completed": 1
                }
            )
        )


        completed_quizzes = []

        for quiz in quiz_documents:

            if quiz.get(
                "completed",
                True
            ):

                completed_quizzes.append(
                    quiz
                )


        quizzes_completed = len(
            completed_quizzes
        )


        # ----------------------------------------------------
        # Average quiz score
        # ----------------------------------------------------

        scores = []


        for quiz in completed_quizzes:

            score = quiz.get(
                "score"
            )

            if score is None:
                continue


            try:

                scores.append(
                    float(score)
                )

            except (
                TypeError,
                ValueError
            ):

                continue


        if scores:

            average_quiz_score = round(
                sum(scores) / len(scores),
                1
            )

        else:

            average_quiz_score = 0


        # ====================================================
        # 3. BUILD RESULT
        # ====================================================

        stats = {

            "userId": user_id,

            "talksWatched": len(
                watched_talks
            ),

            "talksCompleted": talks_completed,

            "minutesViewed": minutes_viewed,

            "quizzesCompleted":
                quizzes_completed,

            "averageQuizScore":
                average_quiz_score
        }


        # ====================================================
        # 4. RETURN
        # ====================================================

        return response(
            200,
            stats
        )


    except Exception as e:

        logger.exception(
            "Error retrieving learning stats"
        )

        return response(
            500,
            {
                "error":
                    "Internal server error",

                "details":
                    str(e)
            }
        )

    finally:

        if client is not None:

            client.close()


# ============================================================
# RESPONSE
# ============================================================

def response(
    status_code,
    body
):

    return {

        "statusCode":
            status_code,

        "headers": {

            "Content-Type":
                "application/json",

            "Access-Control-Allow-Origin":
                "*"
        },

        "body":
            json.dumps(
                body,
                ensure_ascii=False
            )
    }