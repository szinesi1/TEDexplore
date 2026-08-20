# ============================================================
# TEDexplore - Generate Recommendations (Simplified)
#
# Input S3:
#     final_list.csv
#     tags.csv
#     related_videos.csv
#
# Output MongoDB:
#     tedx_videos
#     tedx_watch_next
#
# Recommendation criteria:
#
#     +5  related video
#     +3  each common tag
#
# ============================================================

import sys

from pyspark.sql import functions as F
from pyspark.sql.window import Window

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame


# ============================================================
# 1. JOB INITIALIZATION
# ============================================================

args = getResolvedOptions(sys.argv, ["JOB_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# ============================================================
# 2. CONFIGURATION
# ============================================================

BASE_PATH = "s3://tedexplore-2026-data-sz"

FINAL_LIST_PATH = f"{BASE_PATH}/final_list.csv"
TAGS_PATH = f"{BASE_PATH}/tags.csv"
RELATED_VIDEOS_PATH = f"{BASE_PATH}/related_videos.csv"

MONGO_CONFIG = {
    "connectionName": "TEDexplore",
    "database": "unibg_tedx_2026"
}

MAX_RECOMMENDATIONS = 10
RELATED_VIDEO_WEIGHT = 5
COMMON_TAG_WEIGHT = 3


# ============================================================
# 3. READ DATASETS
# ============================================================

print("Reading final_list.csv...")
final_list_df = spark.read.option("header", True).option("inferSchema", True).csv(FINAL_LIST_PATH)

print("Reading tags.csv...")
tags_df = spark.read.option("header", True).option("inferSchema", True).csv(TAGS_PATH)

print("Reading related_videos.csv...")
related_videos_df = spark.read.option("header", True).option("inferSchema", True).csv(RELATED_VIDEOS_PATH)


# ============================================================
# 4. CLEAN DATASETS
# ============================================================

final_list_clean_df = (
    final_list_df
    .select(F.col("id").alias("video_id"), "slug", "speakers", "title", "url")
    .filter(F.col("video_id").isNotNull())
    .dropDuplicates(["video_id"])
)

tags_clean_df = (
    tags_df
    .select(F.col("id").alias("video_id"), "tag")
    .filter(F.col("video_id").isNotNull() & F.col("tag").isNotNull())
    .dropDuplicates(["video_id", "tag"])
)

related_clean_df = (
    related_videos_df
    .select(F.col("id").alias("source_video_id"), F.col("related_id").alias("related_video_id"))
    .filter(F.col("source_video_id").isNotNull() & F.col("related_video_id").isNotNull())
    .dropDuplicates(["source_video_id", "related_video_id"])
)

tags_agg_df = tags_clean_df.groupBy("video_id").agg(F.collect_set("tag").alias("tags"))

tedx_videos_df = (
    final_list_clean_df
    .join(tags_agg_df, on="video_id", how="left")
    .withColumn("tags", F.coalesce(F.col("tags"), F.array().cast("array<string>")))
    .dropDuplicates(["video_id"])
)

print("Total videos:", tedx_videos_df.count())


# ============================================================
# 5. COMMON TAGS BETWEEN VIDEO PAIRS
# ============================================================

tags_a = tags_clean_df.select(F.col("video_id").alias("source_video_id"), "tag")
tags_b = tags_clean_df.select(F.col("video_id").alias("candidate_video_id"), "tag")

common_tags_agg_df = (
    tags_a.join(tags_b, on="tag", how="inner")
    .filter(F.col("source_video_id") != F.col("candidate_video_id"))
    .groupBy("source_video_id", "candidate_video_id")
    .agg(F.countDistinct("tag").alias("common_tag_count"))
)


# ============================================================
# 6. MERGE RELATED-VIDEO + TAG CANDIDATES
# ============================================================

related_candidates_df = (
    related_clean_df
    .select("source_video_id", F.col("related_video_id").alias("candidate_video_id"))
    .withColumn("is_related", F.lit(1))
)

tag_candidates_df = (
    common_tags_agg_df
    .select("source_video_id", "candidate_video_id")
    .withColumn("is_related", F.lit(0))
)

all_candidates_df = (
    related_candidates_df
    .unionByName(tag_candidates_df)
    .groupBy("source_video_id", "candidate_video_id")
    .agg(F.max("is_related").alias("is_related"))
)

recommendations_df = (
    all_candidates_df
    .join(common_tags_agg_df, on=["source_video_id", "candidate_video_id"], how="left")
    .withColumn("common_tag_count", F.coalesce(F.col("common_tag_count"), F.lit(0)))
)


# ============================================================
# 7. SCORE + REASONS
# ============================================================

recommendations_df = recommendations_df.withColumn(
    "score",
    (F.col("is_related") * F.lit(RELATED_VIDEO_WEIGHT)) +
    (F.col("common_tag_count") * F.lit(COMMON_TAG_WEIGHT))
)

recommendations_df = (
    recommendations_df
    .withColumn("reason_related", F.when(F.col("is_related") == 1, F.lit("related_video")))
    .withColumn("reason_tags", F.when(F.col("common_tag_count") > 0, F.lit("common_tags")))
    .withColumn(
        "reasons",
        F.expr("filter(array(reason_related, reason_tags), x -> x is not null)")
    )
)


# ============================================================
# 8. RANK TOP 10 PER VIDEO
# ============================================================

ranking_window = (
    Window.partitionBy("source_video_id")
    .orderBy(F.col("score").desc(), F.col("candidate_video_id").asc())
)

recommendations_ranked_df = (
    recommendations_df
    .withColumn("rank", F.row_number().over(ranking_window))
    .filter(F.col("rank") <= MAX_RECOMMENDATIONS)
)


# ============================================================
# 9. BUILD tedx_watch_next
# ============================================================

watch_next_df = (
    recommendations_ranked_df
    .select(
        "source_video_id",
        F.struct(
            F.col("candidate_video_id").alias("video_id"),
            F.col("score").cast("double").alias("score"),
            F.col("reasons").alias("reasons")
        ).alias("recommendation")
    )
    .groupBy("source_video_id")
    .agg(F.collect_list("recommendation").alias("recommendations"))
    .select(F.col("source_video_id").alias("_id"), "recommendations")
)


# ============================================================
# 10. WRITE TO MONGODB
# ============================================================

videos_dyf = DynamicFrame.fromDF(tedx_videos_df, glueContext, "tedx_videos")
watch_next_dyf = DynamicFrame.fromDF(watch_next_df, glueContext, "tedx_watch_next")

glueContext.write_dynamic_frame.from_options(
    frame=videos_dyf,
    connection_type="mongodb",
    connection_options={**MONGO_CONFIG, "collection": "tedx_videos"}
)

glueContext.write_dynamic_frame.from_options(
    frame=watch_next_dyf,
    connection_type="mongodb",
    connection_options={**MONGO_CONFIG, "collection": "tedx_watch_next"}
)

print("TEDexplore Recommendation Job (simplified) COMPLETED")

job.commit()
