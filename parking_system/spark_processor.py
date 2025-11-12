from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, current_timestamp, window, 
    count, sum as _sum, avg, min as _min, max as _max,
    expr, when, lit, to_json, struct, hour, from_unixtime,
    udf, broadcast
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    TimestampType, DoubleType, MapType
)
import json

# Configuration
KAFKA_BOOTSTRAP_SERVERS = "192.168.80.57:9093"
INPUT_TOPIC = "parking-events"
OUTPUT_TOPIC = "parking-processed"
CHECKPOINT_LOCATION = "hdfs://192.168.80.57:9000/db_hw02/checkpoints"
PRICING_CONFIG_PATH = "hdfs://192.168.80.57:9000/db_hw02/config/parking_pricing.json"

parking_schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("timestamp_unix", IntegerType(), True),
    StructField("license_plate", StringType(), True),
    StructField("location", StringType(), True),
    StructField("status_code", StringType(), True),
    StructField("entry_timestamp", IntegerType(), True),
    StructField("customer_name", StringType(), True),
    StructField("area", StringType(), True),
    StructField("car_type", StringType(), True)
])


def load_pricing_config(spark, config_path):
    # Read JSON file from HDFS
    df = spark.read.option("multiline", "true").json(config_path)
    config_json = df.toJSON().collect()[0]
    config = json.loads(config_json)
    
    print("Pricing configuration loaded successfully!")
    return config


def create_pricing_broadcast(spark, pricing_config):
    """Create broadcast variable for pricing configuration"""
    return spark.sparkContext.broadcast(pricing_config)


def create_spark_session():
    """Create and configure Spark session with Kafka and Hadoop support"""
    return SparkSession.builder \
        .appName("ParkingEventProcessor") \
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_LOCATION) \
        .config("spark.sql.streaming.stateStore.providerClass", 
                "org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider") \
        .config("spark.sql.streaming.stateStore.stateSchemaCheck", "false") \
        .config("spark.jars.packages", 
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .getOrCreate()


def read_from_kafka(spark):
    """Read streaming data from Kafka"""
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", INPUT_TOPIC) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()


def parse_parking_events(df):
    """Parse JSON data from Kafka value column"""
    return df.select(
        col("key").cast("string").alias("kafka_key"),
        from_json(col("value").cast("string"), parking_schema).alias("data"),
        col("timestamp").alias("kafka_timestamp")
    ).select(
        "kafka_key",
        "kafka_timestamp",
        "data.*"
    )


def calculate_hourly_rate(hour_val, pricing_config):
    """Calculate rate based on hour of day"""
    rates = pricing_config["pricing_rules"]["time_based_rates"]
    
    for rate_rule in rates:
        start = rate_rule["start_hour"]
        end = rate_rule["end_hour"]
        
        if end == 24:
            end = 0
        
        if start < end:
            if start <= hour_val < end:
                return float(rate_rule["rate_per_hour"])
        else:  # Wraps around midnight
            if hour_val >= start or hour_val < end:
                return float(rate_rule["rate_per_hour"])
    
    return 12000.0  # Default rate


def calculate_parking_fee(entry_ts, exit_ts, car_type, floor, pricing_config):
    """Calculate total parking fee"""
    pricing_rules = pricing_config["pricing_rules"]
    
    # Calculate duration in hours
    duration_seconds = exit_ts - entry_ts
    duration_hours = duration_seconds / 3600.0
    
    # Get multipliers
    car_multiplier = pricing_rules["car_type_multipliers"].get(car_type, 1.0)
    floor_multiplier = pricing_rules["floor_multipliers"].get(floor, 1.0)
    
    # Calculate base fee (simplified - using average rate for now)
    # In production, you'd calculate hour-by-hour
    avg_rate = 12000.0  # You can calculate weighted average based on time slots
    base_fee = duration_hours * avg_rate
    
    # Apply multipliers
    total_fee = base_fee * car_multiplier * floor_multiplier
    
    return float(total_fee)


def calculate_parking_metrics(df, pricing_broadcast):
    """
    Calculate stateful metrics for each vehicle with pricing
    """
    # Convert timestamp string to actual timestamp
    df = df.withColumn("event_time", 
                       expr("to_timestamp(timestamp, 'yyyy-MM-dd HH:mm:ss')"))
    
    # Calculate parking duration in minutes
    df = df.withColumn("parking_duration_minutes",
                       expr("(timestamp_unix - entry_timestamp) / 60"))
    
    # Add floor information extracted from location
    df = df.withColumn("floor", expr("substring(location, 1, 1)"))
    
    # Add hour of day for rate calculation
    df = df.withColumn("event_hour", hour(col("event_time")))
    
    # Calculate total parked time and status changes per vehicle
    vehicle_metrics = df.groupBy("license_plate") \
        .agg(
            _max("event_time").alias("last_update"),
            _max("timestamp_unix").alias("last_timestamp"),
            _max("status_code").alias("current_status"),
            _max("location").alias("current_location"),
            _max("parking_duration_minutes").alias("total_parking_minutes"),
            count("*").alias("event_count"),
            _max("customer_name").alias("customer_name"),
            _max("area").alias("area"),
            _max("car_type").alias("car_type"),
            _max("floor").alias("floor"),
            _min("entry_timestamp").alias("first_entry"),
            _max("event_hour").alias("current_hour")
        )
    
    # Create UDF for fee calculation
    pricing_config = pricing_broadcast.value
    
    def calculate_fee_udf(entry_ts, exit_ts, car_type, floor):
        if entry_ts is None or exit_ts is None:
            return 0.0
        return calculate_parking_fee(entry_ts, exit_ts, car_type, floor, pricing_config)
    
    fee_udf = udf(calculate_fee_udf, DoubleType())
    
    # Calculate parking fee
    vehicle_metrics = vehicle_metrics.withColumn(
        "parking_fee",
        fee_udf(
            col("first_entry"),
            col("last_timestamp"),
            col("car_type"),
            col("floor")
        )
    )
    
    # Add computed fields
    vehicle_metrics = vehicle_metrics.withColumn(
        "is_currently_parked",
        when(col("current_status") == "PARKED", lit(True)).otherwise(lit(False))
    ).withColumn(
        "parking_status",
        when(col("current_status") == "ENTERING", lit("Arriving"))
        .when(col("current_status") == "PARKED", lit("Parked"))
        .when(col("current_status") == "MOVING", lit("Leaving Soon"))
        .when(col("current_status") == "EXITING", lit("Exited"))
        .otherwise(lit("Unknown"))
    ).withColumn(
        "currency",
        lit(pricing_config["pricing_rules"]["currency"])
    )
    
    # Calculate hourly rate for current time
    def get_hourly_rate_udf(hour_val):
        if hour_val is None:
            return 12000.0
        return calculate_hourly_rate(hour_val, pricing_config)
    
    rate_udf = udf(get_hourly_rate_udf, DoubleType())
    
    vehicle_metrics = vehicle_metrics.withColumn(
        "current_hourly_rate",
        rate_udf(col("current_hour"))
    )
    
    return vehicle_metrics


def calculate_aggregate_statistics(df):
    """
    Calculate aggregate statistics across all vehicles with revenue
    """
    # Aggregate by status
    status_stats = df.groupBy("current_status") \
        .agg(
            count("*").alias("vehicle_count"),
            avg("total_parking_minutes").alias("avg_parking_minutes"),
            _sum("parking_fee").alias("total_revenue"),
            avg("parking_fee").alias("avg_fee")
        ).withColumn("metric_type", lit("by_status"))
    
    # Aggregate by floor
    floor_stats = df.groupBy("floor") \
        .agg(
            count("*").alias("vehicle_count"),
            avg("total_parking_minutes").alias("avg_parking_minutes"),
            _sum("parking_fee").alias("total_revenue"),
            avg("parking_fee").alias("avg_fee")
        ).withColumn("metric_type", lit("by_floor")) \
        .withColumnRenamed("floor", "current_status")
    
    # Aggregate by car type
    car_type_stats = df.groupBy("car_type") \
        .agg(
            count("*").alias("vehicle_count"),
            avg("total_parking_minutes").alias("avg_parking_minutes"),
            _sum("parking_fee").alias("total_revenue"),
            avg("parking_fee").alias("avg_fee")
        ).withColumn("metric_type", lit("by_car_type")) \
        .withColumnRenamed("car_type", "current_status")
    
    return status_stats, floor_stats, car_type_stats


def prepare_output_for_kafka(df):
    """Prepare DataFrame for writing to Kafka (key-value format)"""
    return df.select(
        col("license_plate").alias("key"),
        to_json(struct("*")).alias("value")
    )


def write_to_kafka(df, query_name, output_mode="update"):
    """Write streaming data to Kafka output topic"""
    return df.writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("topic", OUTPUT_TOPIC) \
        .option("checkpointLocation", f"{CHECKPOINT_LOCATION}/{query_name}") \
        .outputMode(output_mode) \
        .start()


def write_to_console(df, query_name):
    """Write streaming data to console for debugging"""
    return df.writeStream \
        .format("console") \
        .option("truncate", "false") \
        .option("numRows", 20) \
        .outputMode("update") \
        .queryName(query_name) \
        .start()


def main():
    """Main function to run the Spark streaming application"""
    
    # Create Spark session
    print("Creating Spark session...")
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"Reading from Kafka topic: {INPUT_TOPIC}")
    print(f"Checkpoint location: {CHECKPOINT_LOCATION}")
    print(f"Output topic: {OUTPUT_TOPIC}")
    
    # Load pricing configuration
    print(f"\nLoading pricing configuration from: {PRICING_CONFIG_PATH}")
    pricing_config = load_pricing_config(spark, PRICING_CONFIG_PATH)
    pricing_broadcast = create_pricing_broadcast(spark, pricing_config)
    
    print(f"Currency: {pricing_config['pricing_rules']['currency']}")
    
    # Read from Kafka
    raw_stream = read_from_kafka(spark)
    
    # Parse JSON data
    parsed_stream = parse_parking_events(raw_stream)
    
    # Calculate vehicle-level metrics with pricing (stateful)
    vehicle_metrics = calculate_parking_metrics(parsed_stream, pricing_broadcast)
    
    # Prepare for Kafka output
    kafka_output = prepare_output_for_kafka(vehicle_metrics)
    
    # Start streaming queries
    print("\nStarting streaming queries...")
    
    # Query 1: Write vehicle metrics to Kafka
    query_kafka = write_to_kafka(kafka_output, "vehicle_metrics_to_kafka")
    
    # Query 2: Write to console for monitoring (optional)
    query_console = write_to_console(vehicle_metrics, "vehicle_metrics_console")
    
    print("\nStreaming queries started successfully!")
    print(f"Vehicle metrics with pricing are being written to Kafka topic: {OUTPUT_TOPIC}")
    print("Press Ctrl+C to stop...")
    
    # Wait for termination
    try:
        query_kafka.awaitTermination()
    except KeyboardInterrupt:
        print("\nStopping queries...")
        query_kafka.stop()
        query_console.stop()
        spark.stop()
        print("Application stopped successfully!")


if __name__ == "__main__":
    main()