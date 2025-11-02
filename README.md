# Kafka Streaming Applications

A collection of Kafka producer applications for generating streaming data scenarios.

## Projects

| Project | Description | Kafka Topic |
|---------|-------------|-------------|
| **E-commerce** | Order lifecycle events | `ecommerce-orders` |
| **IoT Sensor** | Smart building sensor data | `iot-sensor-data` |
| **Social Media** | Social platform activity events | `social-media-events` |
| **Parking System** | Parking management | `parking-events` |

## Usage

Each project can be run independently:

```bash
cd <project-directory>
python producer.py
```

## Note 

Processing: PySpark

GUI: Flask, Flask-SocketIO

## Configuration

Update `KAFKA_BOOTSTRAP_SERVERS` in each producer script with your Kafka server address.

