import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    user_id = event.get("userId")

    logger.info(f"Retrieving recommended quiz for {user_id}")

    recommendation = {
        "quizId": "QUIZ001",
        "title": "Artificial Intelligence Basics",
        "reason": "related_to_recent_views"
    }

    return {
        "statusCode": 200,
        "body": json.dumps(recommendation)
    }