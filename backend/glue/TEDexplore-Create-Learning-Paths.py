# ============================================================
# TEDexplore - Create Learning Paths
#
# Punto b) Homework 2 - Funzionalita' dalla board:
# "Percorsi tematici"
#
# Raggruppa i talk per tag dominante, creando una prima
# versione (v1) dei percorsi formativi. Non include ancora
# quiz per singolo talk ne' test finale.
#
# Input S3:
#     final_list.csv
#     tags.csv
#
# Output MongoDB:
#     tedx_paths
# ============================================================

import sys

from pyspark.sql import functions as F

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

MONGO_CONFIG = {
    "connectionName": "TEDexplore",
    "database": "unibg_tedx_2026"
}

# Numero minimo di talk per considerare un tag un "percorso" valido
MIN_VIDEOS_PER_PATH = 3


# ============================================================
# 3. READ DATASETS
# ============================================================

print("")
print("============================================================")
print("TEDexplore - Create Learning Paths")
print("============================================================")
print("")

print("Reading final_list.csv...")

final_list_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(FINAL_LIST_PATH)
)

print("Reading tags.csv...")

tags_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(TAGS_PATH)
)


# ============================================================
# 4. CLEAN DATASETS
# ============================================================

final_list_clean_df = (
    final_list_df
    .select(
        F.col("id").alias("video_id"),
        F.col("title")
    )
    .filter(F.col("video_id").isNotNull())
    .dropDuplicates(["video_id"])
)

tags_clean_df = (
    tags_df
    .select(
        F.col("id").alias("video_id"),
        F.col("tag")
    )
    .filter(
        F.col("video_id").isNotNull() &
        F.col("tag").isNotNull()
    )
    .dropDuplicates(["video_id", "tag"])
)


# ============================================================
# 5. ENRICH TAGS WITH VIDEO TITLE
# ============================================================

tags_enriched_df = (
    tags_clean_df
    .join(
        final_list_clean_df,
        on="video_id",
        how="left"
    )
)


# ============================================================
# 6. BUILD LEARNING PATHS (GROUP BY TAG)
# ============================================================

print("")
print("Building learning paths...")
print("")

paths_df = (
    tags_enriched_df
    .groupBy("tag")
    .agg(
        F.collect_set("video_id").alias("video_ids"),
        F.collect_set("title").alias("video_titles"),
        F.countDistinct("video_id").alias("video_count")
    )
    .filter(
        F.col("video_count") >= MIN_VIDEOS_PER_PATH
    )
)

paths_df = (
    paths_df
    .withColumn("_id", F.col("tag"))
    .withColumn(
        "title",
        F.concat(F.lit("Percorso: "), F.col("tag"))
    )
    .select(
        "_id",
        "title",
        "video_ids",
        "video_titles",
        "video_count"
    )
)

print("Total learning paths created:", paths_df.count())


# ============================================================
# 7. CONVERT TO DYNAMIC FRAME
# ============================================================

paths_dyf = DynamicFrame.fromDF(
    paths_df,
    glueContext,
    "tedx_paths"
)


# ============================================================
# 8. WRITE tedx_paths
# ============================================================

print("")
print("Writing tedx_paths...")
print("")

glueContext.write_dynamic_frame.from_options(
    frame=paths_dyf,
    connection_type="mongodb",
    connection_options={
        **MONGO_CONFIG,
        "collection": "tedx_paths"
    }
)

# ============================================================
# 9. SUMMARY
# ============================================================

print("")
print("============================================================")
print("TEDexplore Learning Paths Job COMPLETED")
print("============================================================")
print("")
print("Collection generated: tedx_paths")
print("Minimum videos per path:", MIN_VIDEOS_PER_PATH)
print("")
print("============================================================")

# ============================================================
# 10. COMMIT
# ============================================================

job.commit()
