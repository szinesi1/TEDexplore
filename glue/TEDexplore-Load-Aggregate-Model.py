###### TEDexplore-Load-Aggregate-Model

import sys
from pyspark.sql.functions import col, collect_list

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

### INIT JOB
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

### S3 INPUTS
base_path = "s3://tedexplore-2026-data-sz"

final_list_path = f"{base_path}/final_list.csv"
details_path = f"{base_path}/details.csv"
tags_path = f"{base_path}/tags.csv"
images_path = f"{base_path}/images.csv"
videos_path = f"{base_path}/related_videos.csv"

### READ CSVs
final_list_df = spark.read.option("header", True).csv(final_list_path)
details_df = spark.read.option("header", True).csv(details_path)
tags_df = spark.read.option("header", True).csv(tags_path)
images_df = spark.read.option("header", True).csv(images_path)
videos_df = spark.read.option("header", True).csv(videos_path)

### TRANSFORM DETAILS
details_df = details_df.select(
    col("id").alias("id_ref"),
    col("description"),
    col("duration"),
    col("publishedAt")
)

final_list_enriched = final_list_df.join(
    details_df,
    final_list_df.id == details_df.id_ref,
    "left"
).drop("id_ref")

### AGGREGATE TAGS
tags_agg_df = tags_df.groupBy(col("id").alias("id_ref")).agg(
    collect_list("tag").alias("tags")
)

tags_final_df = tags_agg_df.select(
    col("id_ref").alias("_id"),
    col("tags")
)

### CONVERT TO DYNAMIC FRAMES
final_list_dyf = DynamicFrame.fromDF(final_list_enriched, glueContext, "final_list")
details_dyf = DynamicFrame.fromDF(details_df, glueContext, "details")
tags_dyf = DynamicFrame.fromDF(tags_final_df, glueContext, "tags")
images_dyf = DynamicFrame.fromDF(images_df, glueContext, "images")
videos_dyf = DynamicFrame.fromDF(videos_df, glueContext, "videos")


### MONGO CONNECTION CONFIG
mongo_config = {
    "connectionName": "TEDexplore",
    "database": "unibg_tedx_2026"
}


### WRITE TO MONGO (5 COLLECTIONS)
glueContext.write_dynamic_frame.from_options(
    frame=final_list_dyf,
    connection_type="mongodb",
    connection_options={**mongo_config, "collection": "tedx_final_list"}
)

glueContext.write_dynamic_frame.from_options(
    frame=details_dyf,
    connection_type="mongodb",
    connection_options={**mongo_config, "collection": "tedx_details"}
)

glueContext.write_dynamic_frame.from_options(
    frame=tags_dyf,
    connection_type="mongodb",
    connection_options={**mongo_config, "collection": "tedx_tags"}
)

glueContext.write_dynamic_frame.from_options(
    frame=images_dyf,
    connection_type="mongodb",
    connection_options={**mongo_config, "collection": "tedx_images"}
)

glueContext.write_dynamic_frame.from_options(
    frame=videos_dyf,
    connection_type="mongodb",
    connection_options={**mongo_config, "collection": "tedx_related_videos"}
)

job.commit()
