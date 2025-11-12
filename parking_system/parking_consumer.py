# parking_consumer.py
from kafka import KafkaConsumer
import json
import os
from datetime import datetime


BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "192.168.80.57:9093")
TOPIC = "parking-processed"

# Create Kafka consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',
    enable_auto_commit=True,
    group_id='parking-consumer-group'
)

print(f"Kafka Consumer started. Listening to topic '{TOPIC}' on {BOOTSTRAP_SERVERS}")
print("Press Ctrl+C to stop...")
print(f"{'='*80}\n")

try:
    for message in consumer:
        event = message.value
        
        print(f"{'='*80}")
        print(f"New Event Received:", event)

except KeyboardInterrupt:
    print("\nStopping Kafka Consumer...")
    consumer.close()
    print("Stopped.")
