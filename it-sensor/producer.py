import time
import random
import json
import math
from datetime import datetime
from enum import Enum
from kafka import KafkaProducer


class SensorType(Enum):
    """Types of IoT sensors"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    AIR_QUALITY = "air_quality"
    MOTION = "motion"
    LIGHT = "light"
    SOUND = "sound"
    VIBRATION = "vibration"
    PROXIMITY = "proximity"
    DOOR_WINDOW = "door_window"
    WATER_LEVEL = "water_level"
    POWER_CONSUMPTION = "power_consumption"
    HEART_RATE = "heart_rate"
    GPS_LOCATION = "gps_location"


class SensorStatus(Enum):
    """Sensor operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    ERROR = "error"
    CALIBRATING = "calibrating"


class AlertLevel(Enum):
    """Alert severity levels"""
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SmartBuildingSensor:
    """Class representing an IoT sensor in a smart building"""

    # Building zones
    ZONES = {
        "Floor1": ["Lobby", "Reception", "Meeting_Room_A", "Office_1A", "Office_1B", "Cafeteria"],
        "Floor2": ["Office_2A", "Office_2B", "Office_2C", "Conference_Room", "Server_Room", "Storage"],
        "Floor3": ["Office_3A", "Office_3B", "Office_3C", "Executive_Suite", "Training_Room", "Restroom"],
        "Floor4": ["R&D_Lab", "Testing_Area", "Workshop", "Clean_Room", "Equipment_Room", "Archive"],
        "Basement": ["Parking", "Maintenance", "Electrical_Room", "HVAC_Room", "Storage_B", "Security"]
    }

    # Sensor deployment by zone type
    SENSOR_CONFIGS = {
        "Office": [SensorType.TEMPERATURE, SensorType.HUMIDITY, SensorType.LIGHT, 
                   SensorType.MOTION, SensorType.AIR_QUALITY, SensorType.POWER_CONSUMPTION],
        "Meeting": [SensorType.TEMPERATURE, SensorType.HUMIDITY, SensorType.LIGHT, 
                    SensorType.MOTION, SensorType.AIR_QUALITY, SensorType.SOUND],
        "Server": [SensorType.TEMPERATURE, SensorType.HUMIDITY, SensorType.VIBRATION,
                   SensorType.POWER_CONSUMPTION, SensorType.DOOR_WINDOW],
        "Common": [SensorType.TEMPERATURE, SensorType.HUMIDITY, SensorType.LIGHT,
                   SensorType.MOTION, SensorType.AIR_QUALITY],
        "Parking": [SensorType.MOTION, SensorType.LIGHT, SensorType.PROXIMITY, SensorType.DOOR_WINDOW],
        "Mechanical": [SensorType.TEMPERATURE, SensorType.VIBRATION, SensorType.SOUND,
                       SensorType.POWER_CONSUMPTION, SensorType.DOOR_WINDOW]
    }

    def __init__(self, sensor_id, floor, room, sensor_type):
        self.sensor_id = sensor_id
        self.floor = floor
        self.room = room
        self.sensor_type = sensor_type
        self.status = SensorStatus.ONLINE
        
        # Base values with some variability
        self.base_temperature = random.uniform(20, 24)
        self.base_humidity = random.uniform(40, 60)
        self.base_pressure = random.uniform(1010, 1020)
        self.base_air_quality = random.uniform(50, 150)
        
        # Anomaly simulation
        self.anomaly_active = False
        self.anomaly_duration = 0
        self.anomaly_counter = 0
        
        # Battery for wireless sensors
        self.battery_level = random.uniform(85, 100)
        self.battery_drain_rate = random.uniform(0.0001, 0.0005)
        
        # Last reading timestamp
        self.last_reading_time = int(time.time())

    def simulate_anomaly(self):
        """Randomly trigger sensor anomalies"""
        if not self.anomaly_active and random.random() < 0.005:  # 0.5% chance
            self.anomaly_active = True
            self.anomaly_duration = random.randint(5, 30)
            self.anomaly_counter = 0
            
        if self.anomaly_active:
            self.anomaly_counter += 1
            if self.anomaly_counter >= self.anomaly_duration:
                self.anomaly_active = False
                self.anomaly_counter = 0

    def get_reading(self):
        """Generate sensor reading based on type"""
        current_time = int(time.time())
        time_diff = current_time - self.last_reading_time
        
        # Simulate battery drain
        self.battery_level -= self.battery_drain_rate * time_diff
        if self.battery_level < 0:
            self.battery_level = 0
            self.status = SensorStatus.OFFLINE
        elif self.battery_level < 20:
            self.status = SensorStatus.WARNING
        
        # Check for anomalies
        self.simulate_anomaly()
        
        # Generate reading based on sensor type
        reading = {}
        alert_level = AlertLevel.NORMAL
        
        if self.sensor_type == SensorType.TEMPERATURE:
            # Add daily cycle (warmer during day)
            hour = datetime.now().hour
            daily_variation = 2 * math.sin((hour - 6) * math.pi / 12)
            
            temp = self.base_temperature + daily_variation + random.uniform(-0.5, 0.5)
            
            if self.anomaly_active:
                temp += random.uniform(5, 15)  # Significant temperature spike
            
            reading = {"value": round(temp, 2), "unit": "°C"}
            
            if temp > 28:
                alert_level = AlertLevel.HIGH
            elif temp > 26:
                alert_level = AlertLevel.MEDIUM
            elif temp < 18:
                alert_level = AlertLevel.MEDIUM
                
        elif self.sensor_type == SensorType.HUMIDITY:
            humidity = self.base_humidity + random.uniform(-3, 3)
            
            if self.anomaly_active:
                humidity += random.uniform(20, 40)
            
            humidity = max(0, min(100, humidity))
            reading = {"value": round(humidity, 2), "unit": "%"}
            
            if humidity > 70:
                alert_level = AlertLevel.HIGH
            elif humidity > 65 or humidity < 30:
                alert_level = AlertLevel.MEDIUM
                
        elif self.sensor_type == SensorType.PRESSURE:
            pressure = self.base_pressure + random.uniform(-2, 2)
            reading = {"value": round(pressure, 2), "unit": "hPa"}
            
        elif self.sensor_type == SensorType.AIR_QUALITY:
            # PM2.5 Air Quality Index
            aqi = self.base_air_quality + random.uniform(-10, 10)
            
            if self.anomaly_active:
                aqi += random.uniform(100, 300)
            
            aqi = max(0, aqi)
            reading = {"value": round(aqi, 2), "unit": "AQI"}
            
            if aqi > 300:
                alert_level = AlertLevel.CRITICAL
            elif aqi > 200:
                alert_level = AlertLevel.HIGH
            elif aqi > 150:
                alert_level = AlertLevel.MEDIUM
                
        elif self.sensor_type == SensorType.MOTION:
            # Binary sensor with probability of detection
            motion_detected = random.random() < 0.3
            if self.anomaly_active:
                motion_detected = True
            reading = {"detected": motion_detected}
            
        elif self.sensor_type == SensorType.LIGHT:
            # Lux measurement
            hour = datetime.now().hour
            if 6 <= hour <= 18:
                base_light = random.uniform(300, 500)
            else:
                base_light = random.uniform(50, 150)
                
            reading = {"value": round(base_light, 2), "unit": "lux"}
            
        elif self.sensor_type == SensorType.SOUND:
            # Decibel measurement
            sound_level = random.uniform(35, 55)
            
            if self.anomaly_active:
                sound_level = random.uniform(80, 100)
                alert_level = AlertLevel.HIGH
                
            reading = {"value": round(sound_level, 2), "unit": "dB"}
            
        elif self.sensor_type == SensorType.VIBRATION:
            # Acceleration in m/s²
            vibration = random.uniform(0, 0.5)
            
            if self.anomaly_active:
                vibration = random.uniform(5, 15)
                alert_level = AlertLevel.CRITICAL
                
            reading = {"value": round(vibration, 3), "unit": "m/s²"}
            
            if vibration > 2:
                alert_level = AlertLevel.HIGH
            elif vibration > 1:
                alert_level = AlertLevel.MEDIUM
                
        elif self.sensor_type == SensorType.PROXIMITY:
            # Distance in meters
            distance = random.uniform(0.1, 5.0)
            reading = {"value": round(distance, 2), "unit": "m"}
            
        elif self.sensor_type == SensorType.DOOR_WINDOW:
            # Open/Closed status
            is_open = random.random() < 0.1
            if self.anomaly_active:
                is_open = True
                alert_level = AlertLevel.MEDIUM
            reading = {"open": is_open}
            
        elif self.sensor_type == SensorType.WATER_LEVEL:
            # Water level in cm
            level = random.uniform(0, 10)
            if self.anomaly_active:
                level = random.uniform(50, 100)
                alert_level = AlertLevel.CRITICAL
            reading = {"value": round(level, 2), "unit": "cm"}
            
        elif self.sensor_type == SensorType.POWER_CONSUMPTION:
            # Power in kWh
            hour = datetime.now().hour
            if 8 <= hour <= 18:
                power = random.uniform(5, 15)
            else:
                power = random.uniform(1, 5)
                
            if self.anomaly_active:
                power = random.uniform(30, 50)
                alert_level = AlertLevel.HIGH
                
            reading = {"value": round(power, 3), "unit": "kWh"}
            
        elif self.sensor_type == SensorType.HEART_RATE:
            # BPM
            hr = random.uniform(60, 100)
            reading = {"value": round(hr, 0), "unit": "bpm"}
            
        elif self.sensor_type == SensorType.GPS_LOCATION:
            # Simulate location (example coordinates)
            lat = 10.8231 + random.uniform(-0.001, 0.001)
            lon = 106.6297 + random.uniform(-0.001, 0.001)
            reading = {
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "accuracy": round(random.uniform(5, 20), 2)
            }
        
        self.last_reading_time = current_time
        
        return reading, alert_level

    def get_event_info(self):
        """Return complete sensor event information"""
        reading, alert_level = self.get_reading()
        
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_unix": int(time.time()),
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type.value,
            "location": {
                "floor": self.floor,
                "room": self.room
            },
            "reading": reading,
            "status": self.status.value,
            "alert_level": alert_level.value,
            "battery_level": round(self.battery_level, 2),
            "anomaly_detected": self.anomaly_active
        }
        
        return event


def generate_sensor_network():
    """Generate a network of sensors across the building"""
    sensors = []
    sensor_id_counter = 1
    
    for floor, rooms in SmartBuildingSensor.ZONES.items():
        for room in rooms:
            # Determine zone type
            if "Office" in room or "Executive" in room:
                zone_type = "Office"
            elif "Meeting" in room or "Conference" in room or "Training" in room:
                zone_type = "Meeting"
            elif "Server" in room:
                zone_type = "Server"
            elif "Parking" in room:
                zone_type = "Parking"
            elif "HVAC" in room or "Electrical" in room or "Maintenance" in room:
                zone_type = "Mechanical"
            else:
                zone_type = "Common"
            
            # Deploy appropriate sensors
            sensor_types = SmartBuildingSensor.SENSOR_CONFIGS[zone_type]
            
            for sensor_type in sensor_types:
                sensor_id = f"SNS{sensor_id_counter:05d}"
                sensor = SmartBuildingSensor(sensor_id, floor, room, sensor_type)
                sensors.append(sensor)
                sensor_id_counter += 1
    
    return sensors


def iot_sensor_stream_to_kafka(
    kafka_bootstrap_servers,
    kafka_topic,
    duration_minutes=30,
    readings_per_second=20
):
    """
    Stream IoT sensor data to Kafka
    
    Args:
        kafka_bootstrap_servers: Kafka server address
        kafka_topic: Topic name to publish events
        duration_minutes: How long to run the stream
        readings_per_second: Target number of sensor readings per second
    """
    
    # Initialize Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    event_interval = 1.0 / readings_per_second

    # Generate sensor network
    print("Initializing sensor network...")
    sensors = generate_sensor_network()
    print(f"Deployed {len(sensors)} sensors across the building")
    
    # Statistics
    total_readings = 0
    alert_counts = {level: 0 for level in AlertLevel}
    sensor_type_counts = {stype: 0 for stype in SensorType}

    try:
        print(f"\nStarting IoT Sensor Stream to Kafka topic: {kafka_topic}")
        print(f"Kafka server: {kafka_bootstrap_servers}")
        print(f"Target rate: {readings_per_second} readings/second")
        print("-" * 100)

        while time.time() < end_time:
            # Randomly select a sensor to read
            sensor = random.choice(sensors)
            
            # Get sensor reading
            event_data = sensor.get_event_info()
            
            # Send to Kafka (key = sensor_id for partitioning)
            producer.send(
                kafka_topic,
                key=event_data['sensor_id'],
                value=event_data
            )
            
            # Update statistics
            total_readings += 1
            alert_counts[AlertLevel[event_data['alert_level'].upper()]] += 1
            sensor_type_counts[SensorType[event_data['sensor_type'].upper()]] += 1
            
            # Print to console
            if total_readings % 100 == 0:  # Summary every 100 readings
                elapsed = time.time() - start_time
                rate = total_readings / elapsed if elapsed > 0 else 0
                alerts = sum(alert_counts[level] for level in [AlertLevel.MEDIUM, AlertLevel.HIGH, AlertLevel.CRITICAL])
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Readings: {total_readings} | "
                      f"Rate: {rate:.1f}/s | Alerts: {alerts}")
            else:
                # Print individual reading
                alert_indicator = "⚠️ " if event_data['alert_level'] != 'normal' else "   "
                print(f"{alert_indicator}{event_data['timestamp']} | {event_data['sensor_id']} | "
                      f"{event_data['sensor_type']:20} | {event_data['location']['floor']:10} | "
                      f"{event_data['location']['room']:20} | Alert: {event_data['alert_level']:8}")
            
            # Sleep to maintain target rate
            time.sleep(event_interval)

    except KeyboardInterrupt:
        print("\n\nStopping stream...")
    finally:
        producer.flush()
        producer.close()
        
        elapsed = time.time() - start_time
        print(f"\n{'='*100}")
        print(f"IoT Sensor Stream Summary:")
        print(f"{'='*100}")
        print(f"Total Readings: {total_readings}")
        print(f"Duration: {elapsed:.2f} seconds")
        print(f"Average Rate: {total_readings/elapsed:.2f} readings/second")
        
        print(f"\nAlert Level Distribution:")
        for level, count in sorted(alert_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_readings * 100) if total_readings > 0 else 0
            print(f"  {level.value:15} : {count:6} ({percentage:.1f}%)")
        
        print(f"\nTop Sensor Types:")
        for stype, count in sorted(sensor_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            percentage = (count / total_readings * 100) if total_readings > 0 else 0
            print(f"  {stype.value:20} : {count:6} ({percentage:.1f}%)")
        
        print(f"\nKafka Producer closed")


if __name__ == "__main__":
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS = '192.168.1.56:9092'
    KAFKA_TOPIC = 'iot-sensor-data'

    # Stream for 30 minutes with 20 readings per second
    # This simulates ~36,000 sensor readings in 30 minutes
    iot_sensor_stream_to_kafka(
        kafka_bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        kafka_topic=KAFKA_TOPIC,
        duration_minutes=30,
        readings_per_second=20
    )