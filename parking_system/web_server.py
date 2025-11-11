# web_server.py
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from kafka import KafkaConsumer
import json
import threading
from datetime import datetime
from collections import defaultdict, deque

KAFKA_BOOTSTRAP_SERVERS = '192.168.80.57:9093'
KAFKA_TOPIC = 'parking-events'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'parking_lot_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

parking_state = {
    'vehicles': {},  
    'locations': {},  
    'stats': {
        'total_parked': 0,
        'total_fee': 0,
        'available_spots': 60
    },
    'events': deque(maxlen=100) 
}

PARKING_FEE_PER_MINUTE = 3000 # fee/m
TOTAL_SPOTS = 60

def calculate_fee(entry_timestamp, current_timestamp):
    minutes = int((current_timestamp - entry_timestamp) / 60)
    return minutes * PARKING_FEE_PER_MINUTE, minutes

def process_kafka_messages():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True
    )
    
    print(f"✅ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    
    for message in consumer:
        data = message.value
        license_plate = data['license_plate']
        location = data['location']
        status = data['status_code']
        timestamp = data['timestamp_unix']
        entry_timestamp = data['entry_timestamp']
        
        event_log = {
            'timestamp': data['timestamp'],
            'license_plate': license_plate,
            'location': location,
            'status': status,
            'action': get_action_description(status, license_plate)
        }
        parking_state['events'].appendleft(event_log)
        
        if status == 'ENTERING':
            parking_state['vehicles'][license_plate] = {
                'location': location,
                'entry_timestamp': entry_timestamp,
                'current_timestamp': timestamp,
                'status': status
            }
            parking_state['locations'][location] = license_plate
            
        elif status == 'PARKED':
            if license_plate in parking_state['vehicles']:
                parking_state['vehicles'][license_plate].update({
                    'current_timestamp': timestamp,
                    'status': status
                })
            else:
                parking_state['vehicles'][license_plate] = {
                    'location': location,
                    'entry_timestamp': entry_timestamp,
                    'current_timestamp': timestamp,
                    'status': status
                }
                parking_state['locations'][location] = license_plate
        
        elif status == 'MOVING':
            if license_plate in parking_state['vehicles']:
                parking_state['vehicles'][license_plate].update({
                    'current_timestamp': timestamp,
                    'status': status
                })
            
        elif status == 'EXITING':
            if license_plate in parking_state['vehicles']:
                loc = parking_state['vehicles'][license_plate]['location']
                # remove
                if loc in parking_state['locations']:
                    parking_state['locations'][loc] = None
                # del
                del parking_state['vehicles'][license_plate]
        
        total_parked = len(parking_state['vehicles'])
        total_fee = 0
        
        for plate, info in parking_state['vehicles'].items():
            fee, _ = calculate_fee(info['entry_timestamp'], info['current_timestamp'])
            total_fee += fee
        
        parking_state['stats'] = {
            'total_parked': total_parked,
            'total_fee': total_fee,
            'available_spots': TOTAL_SPOTS - total_parked
        }
        
        # Broadcast to all connected clients
        socketio.emit('update', get_dashboard_data())

def get_action_description(status, license_plate):
    if status == 'ENTERING':
        return f"🚗 {license_plate} Entering"
    elif status == 'PARKED':
        return f"🅿️ {license_plate} Parked"
    elif status == 'MOVING':
        return f"🚙 {license_plate} Moving"
    elif status == 'EXITING':
        return f"🚦 {license_plate} Existing"
    return f"{license_plate} - {status}"

def get_dashboard_data():
    vehicles_list = []
    
    for plate, info in parking_state['vehicles'].items():
        fee, minutes = calculate_fee(info['entry_timestamp'], info['current_timestamp'])
        vehicles_list.append({
            'license_plate': plate,
            'location': info['location'],
            'minutes': minutes,
            'fee': fee,
            'status': info['status']
        })
    
    vehicles_list.sort(key=lambda x: x['fee'], reverse=True)
    
    floors = defaultdict(list)
    for location, plate in parking_state['locations'].items():
        if plate:
            floor = location[0]
            floors[floor].append({
                'location': location,
                'license_plate': plate
            })
    
    return {
        'stats': parking_state['stats'],
        'vehicles': vehicles_list,
        'floors': dict(floors),
        'events': list(parking_state['events']),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.route('/')
def index():
    return render_template('dashboardv2.html')

@app.route('/api/data')
def get_data():
    return jsonify(get_dashboard_data())

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.emit('update', get_dashboard_data())

if __name__ == '__main__':
    kafka_thread = threading.Thread(target=process_kafka_messages, daemon=True)
    kafka_thread.start()
    
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)