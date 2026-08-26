import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("glue")

# NOTE: verifica che questi nomi corrispondano esattamente
# ai nomi dei job configurati nella console AWS Glue
GLUE_JOB_NAMES = [
    "TEDexplore-Load-Aggregate-Model",
    "TEDexplore-Generate-Recommendations",
]


def lambda_handler(event, context):

    results = []

    for job_name in GLUE_JOB_NAMES:

        try:

            response = client.start_job_run(
                JobName=job_name
            )

            run_id = response["JobRunId"]

            logger.info(f"Started Glue Job: {job_name} (Run ID: {run_id})")

            results.append(
                {
                    "jobName": job_name,
                    "jobRunId": run_id,
                    "status": "STARTED"
                }
            )

        except Exception as e:

            logger.exception(f"Failed to start Glue Job: {job_name}")

            results.append(
                {
                    "jobName": job_name,
                    "error": str(e),
                    "status": "FAILED_TO_START"
                }
            )

    # Se anche un solo job non è partito, segnalalo con un 207/500
    all_started = all(
        result["status"] == "STARTED"
        for result in results
    )

    status_code = 200 if all_started else 207

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(
            {
                "jobs": results
            }
        )
    }
