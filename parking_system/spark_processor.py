from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, current_timestamp, window, 
    count, sum as _sum, avg, min as _min, max as _max,
    expr, when, lit, to_json, struct, hour, from_unixtime
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    TimestampType, DoubleType, MapType
)
from pyspark.sql.streaming import GroupState, GroupStateTimeout
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

output_schema = StructType([
    StructField("license_plate", StringType(), True),
    StructField("last_update", TimestampType(), True),
    StructField("last_timestamp", IntegerType(), True),
    StructField("current_status", StringType(), True),
    StructField("current_location", StringType(), True),
    StructField("total_parking_minutes", DoubleType(), True),
    StructField("event_count", IntegerType(), True),
    StructField("customer_name", StringType(), True),
    StructField("area", StringType(), True),
    StructField("car_type", StringType(), True),
    StructField("floor", StringType(), True),
    StructField("first_entry", IntegerType(), True),
    StructField("current_hour", IntegerType(), True),
    StructField("parking_fee", DoubleType(), True),
    StructField("is_currently_parked", StringType(), True),
    StructField("parking_status", StringType(), True),
    StructField("currency", StringType(), True),
    StructField("current_hourly_rate", DoubleType(), True)
])


def load_pricing_config(spark, config_path):
    df = spark.read.option("multiline", "true").json(config_path)
    config_json = df.toJSON().collect()[0]
    config = json.loads(config_json)
    
    print("Pricing configuration loaded successfully!")
    return config


def create_spark_session():
    spark = SparkSession.builder \
        .appName("ParkingEventProcessor") \
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_LOCATION) \
        .config("spark.sql.streaming.stateStore.providerClass", 
                "org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider") \
        .config("spark.sql.streaming.stateStore.stateSchemaCheck", "false") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    
    return spark


def read_from_kafka(spark):
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", INPUT_TOPIC) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()


def parse_parking_events(df):
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
    rates = pricing_config["pricing_rules"]["time_based_rates"]
    
    for rate_rule in rates:
        start = rate_rule["start_hour"]
        end = rate_rule["end_hour"]
        
        if end == 24:
            end = 0
        
        if start < end:
            if start <= hour_val < end:
                return float(rate_rule["rate_per_hour"])
        else:
            if hour_val >= start or hour_val < end:
                return float(rate_rule["rate_per_hour"])
    
    return 12000.0


def calculate_parking_fee(entry_ts, exit_ts, car_type, floor, pricing_config):
    pricing_rules = pricing_config["pricing_rules"]
    
    duration_seconds = exit_ts - entry_ts
    duration_hours = duration_seconds / 3600.0
    
    car_multiplier = pricing_rules["car_type_multipliers"].get(car_type, 1.0)
    floor_multiplier = pricing_rules["floor_multipliers"].get(floor, 1.0)
    
    avg_rate = 12000.0
    base_fee = duration_hours * avg_rate
    
    total_fee = base_fee * car_multiplier * floor_multiplier
    
    return float(total_fee)


def update_vehicle_state(license_plate, events, state, pricing_config):
    """
    Stateful function to handle deduplication and conflict resolution
    for events from multiple machines
    """
    from datetime import datetime
    
    # Get existing state or initialize
    if state.exists:
        existing = state.get()
    else:
        existing = {
            'last_timestamp': 0,
            'event_count': 0,
            'first_entry': None,
            'current_status': None,
            'current_location': None,
            'customer_name': None,
            'area': None,
            'car_type': None,
            'seen_events': set()
        }
    
    # Sort events by timestamp to process in order
    sorted_events = sorted(events, key=lambda x: (x.timestamp_unix, x.kafka_timestamp))
    
    # Process each event with deduplication
    for event in sorted_events:
        # Create unique event ID for deduplication
        event_id = f"{event.license_plate}_{event.timestamp_unix}_{event.status_code}_{event.location}"
        
        # Skip duplicate events
        if event_id in existing['seen_events']:
            continue
        
        # Add to seen events (keep last 1000 for memory efficiency)
        existing['seen_events'].add(event_id)
        if len(existing['seen_events']) > 1000:
            existing['seen_events'] = set(list(existing['seen_events'])[-1000:])
        
        # Update state only if timestamp is newer or equal (for conflict resolution)
        if event.timestamp_unix >= existing['last_timestamp']:
            # If same timestamp, resolve by status priority: EXITING > MOVING > PARKED > ENTERING
            if event.timestamp_unix == existing['last_timestamp']:
                status_priority = {'EXITING': 4, 'MOVING': 3, 'PARKED': 2, 'ENTERING': 1}
                current_priority = status_priority.get(existing['current_status'], 0)
                new_priority = status_priority.get(event.status_code, 0)
                
                if new_priority <= current_priority:
                    continue
            
            existing['last_timestamp'] = event.timestamp_unix
            existing['current_status'] = event.status_code
            existing['current_location'] = event.location
            existing['customer_name'] = event.customer_name
            existing['area'] = event.area
            existing['car_type'] = event.car_type
            existing['event_count'] += 1
            
            # Set first entry timestamp
            if existing['first_entry'] is None:
                existing['first_entry'] = event.entry_timestamp
    
    # Update state
    state.update(existing)
    
    # Calculate derived metrics
    floor = existing['current_location'][0] if existing['current_location'] else 'A'
    parking_duration_minutes = (existing['last_timestamp'] - existing['first_entry']) / 60.0 if existing['first_entry'] else 0.0
    
    # Calculate parking fee
    parking_fee = 0.0
    if existing['first_entry'] and existing['last_timestamp']:
        parking_fee = calculate_parking_fee(
            existing['first_entry'],
            existing['last_timestamp'],
            existing['car_type'],
            floor,
            pricing_config
        )
    
    # Determine parking status
    status_map = {
        'ENTERING': 'Arriving',
        'PARKED': 'Parked',
        'MOVING': 'Leaving Soon',
        'EXITING': 'Exited'
    }
    parking_status = status_map.get(existing['current_status'], 'Unknown')
    
    # Calculate current hour and hourly rate
    current_hour = datetime.fromtimestamp(existing['last_timestamp']).hour if existing['last_timestamp'] else 0
    current_hourly_rate = calculate_hourly_rate(current_hour, pricing_config)
    
    # Return output row
    return [(
        license_plate,
        datetime.fromtimestamp(existing['last_timestamp']) if existing['last_timestamp'] else None,
        existing['last_timestamp'],
        existing['current_status'],
        existing['current_location'],
        parking_duration_minutes,
        existing['event_count'],
        existing['customer_name'],
        existing['area'],
        existing['car_type'],
        floor,
        existing['first_entry'],
        current_hour,
        parking_fee,
        str(existing['current_status'] == 'PARKED'),
        parking_status,
        pricing_config['pricing_rules']['currency'],
        current_hourly_rate
    )]


def calculate_parking_metrics(df, pricing_config):
    # Add event_time and floor
    df = df.withColumn("event_time", expr("to_timestamp(timestamp, 'yyyy-MM-dd HH:mm:ss')"))
    df = df.withColumn("floor", expr("substring(location, 1, 1)"))
    df = df.withColumn("event_hour", hour(col("event_time")))
    
    # Use mapGroupsWithState for stateful deduplication
    def state_update_func(license_plate, events, state):
        return update_vehicle_state(license_plate, events, state, pricing_config)
    
    vehicle_metrics = df \
        .groupByKey(lambda row: row.license_plate) \
        .mapGroupsWithState(
            state_update_func,
            output_schema,
            output_schema,
            GroupStateTimeout.NoTimeout
        )
    
    return vehicle_metrics


def prepare_output_for_kafka(df):
    return df.select(
        col("license_plate").alias("key"),
        to_json(struct("*")).alias("value")
    )


def write_to_kafka(df, query_name, output_mode="update"):
    return df.writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("topic", OUTPUT_TOPIC) \
        .option("checkpointLocation", f"{CHECKPOINT_LOCATION}/{query_name}") \
        .outputMode(output_mode) \
        .start()


def main():
    spark = create_spark_session()
    
    pricing_config = load_pricing_config(spark, PRICING_CONFIG_PATH)
    
    raw_stream = read_from_kafka(spark)
    parsed_stream = parse_parking_events(raw_stream)
    vehicle_metrics = calculate_parking_metrics(parsed_stream, pricing_config)
    kafka_output = prepare_output_for_kafka(vehicle_metrics)
    query_kafka = write_to_kafka(kafka_output, "vehicle_metrics_to_kafka")
    
    print("\nStarted successfully!\n")
    
    try:
        query_kafka.awaitTermination()
    except KeyboardInterrupt:
        print("\nStopping queries...")
        query_kafka.stop()
        spark.stop()
        print("Application stopped successfully!")


if __name__ == "__main__":
    main()