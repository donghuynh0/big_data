# web_server.py - WebSocket API Server
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
from kafka import KafkaConsumer
import json
import threading
from datetime import datetime
from collections import defaultdict
import redis

app = Flask(__name__)
app.config['SECRET_KEY'] = 'parking_lot_secret'
CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True
)

parking_state = {
    'vehicles': {},
    'locations': {},
    'stats': {
        'total_parked': 0,
        'total_fee': 0,
        'available_spots': 105
    }
}

TOTAL_SPOTS = 105
KAFKA_SERVER = '192.168.80.57:9093'
KAFKA_TOPIC = 'parking-processed'

try:
    redis_client = redis.Redis(
        host='192.168.80.102',
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    print("✅ Connected to Redis")
except Exception as e:
    print(f"⚠️  Redis connection failed: {e}")
    redis_client = None

def save_parking_history(event_type, license_plate, location, customer_name, area, car_type, fee=0, minutes=0, entry_timestamp=None, parking_status=None, currency='VND', hourly_rate=0):
    if not redis_client:
        return
    
    try:
        history_entry = {
            'event_type': event_type,
            'license_plate': license_plate,
            'location': location,
            'customer_name': customer_name,
            'area': area,
            'car_type': car_type,
            'fee': fee,
            'minutes': minutes,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp_unix': int(datetime.now().timestamp()),
            'entry_timestamp': entry_timestamp,
            'parking_status': parking_status,
            'currency': currency,
            'hourly_rate': hourly_rate
        }
        
        redis_client.lpush('parking:history', json.dumps(history_entry))
        redis_client.ltrim('parking:history', 0, 999)
    except Exception as e:
        print(f"❌ Error saving history: {e}")

def process_kafka_messages():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_SERVER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='parking-web-server-group'
    )

    print(f"✅ Connected to Kafka: {KAFKA_SERVER}")
    print(f"📡 Listening to topic: {KAFKA_TOPIC}")

    for message in consumer:
        data = message.value
        
        license_plate = data.get('license_plate')
        location = data.get('current_location')
        status = data.get('current_status')
        parking_status = data.get('parking_status')
        timestamp = data.get('last_timestamp')
        entry_timestamp = data.get('first_entry')
        customer_name = data.get('customer_name', 'Unknown')
        area = data.get('area', 'Unknown')
        car_type = data.get('car_type', 'Normal')
        floor = data.get('floor', 'Unknown')
        
        fee = data.get('parking_fee', 0)
        minutes = data.get('total_parking_minutes', 0)
        currency = data.get('currency', 'VND')
        hourly_rate = data.get('current_hourly_rate', 0)
        is_currently_parked = data.get('is_currently_parked', False)

        if status == 'ENTERING':
            save_parking_history(
                event_type='ENTERING',
                license_plate=license_plate,
                location=location,
                customer_name=customer_name,
                area=area,
                car_type=car_type,
                fee=fee,
                minutes=minutes,
                entry_timestamp=entry_timestamp,
                parking_status=parking_status,
                currency=currency,
                hourly_rate=hourly_rate
            )
        
        elif status == 'PARKED':
            parking_state['vehicles'][license_plate] = {
                'location': location,
                'entry_timestamp': entry_timestamp,
                'current_timestamp': timestamp,
                'status': status,
                'customer_name': customer_name,
                'area': area,
                'car_type': car_type,
                'floor': floor,
                'fee': fee,
                'minutes': minutes,
                'currency': currency,
                'hourly_rate': hourly_rate,
                'parking_status': parking_status
            }
            parking_state['locations'][location] = license_plate
            
            save_parking_history(
                event_type='PARKED',
                license_plate=license_plate,
                location=location,
                customer_name=customer_name,
                area=area,
                car_type=car_type,
                fee=fee,
                minutes=minutes,
                entry_timestamp=entry_timestamp,
                parking_status=parking_status,
                currency=currency,
                hourly_rate=hourly_rate
            )

        elif status == 'EXITING':
            if license_plate in parking_state['vehicles']:
                info = parking_state['vehicles'][license_plate]
                loc = info['location']
                
                save_parking_history(
                    event_type='EXITING',
                    license_plate=license_plate,
                    location=loc,
                    customer_name=customer_name,
                    area=area,
                    car_type=car_type,
                    fee=fee,
                    minutes=minutes,
                    entry_timestamp=entry_timestamp,
                    parking_status=parking_status,
                    currency=currency,
                    hourly_rate=hourly_rate
                )
                
                parking_state['locations'][loc] = None
                del parking_state['vehicles'][license_plate]

        total_parked = len(parking_state['vehicles'])
        total_fee = sum(info.get('fee', 0) for info in parking_state['vehicles'].values())

        parking_state['stats'] = {
            'total_parked': total_parked,
            'total_fee': total_fee,
            'available_spots': TOTAL_SPOTS - total_parked
        }

        try:
            socketio.emit('update', get_dashboard_data())
        except Exception as e:
            print(f"❌ Error broadcasting update: {e}")

def get_dashboard_data():
    try:
        vehicles_list = []

        for plate, info in parking_state['vehicles'].items():
            try:
                vehicles_list.append({
                    'license_plate': plate,
                    'location': info['location'],
                    'minutes': info.get('minutes', 0),
                    'fee': info.get('fee', 0),
                    'customer_name': info.get('customer_name', 'Unknown'),
                    'area': info.get('area', 'Unknown'),
                    'car_type': info.get('car_type', 'Normal'),
                    'floor': info.get('floor', 'Unknown'),
                    'entry_timestamp': info.get('entry_timestamp'),
                    'current_timestamp': info.get('current_timestamp', info.get('entry_timestamp')),
                    'parking_status': info.get('parking_status', 'Unknown'),
                    'currency': info.get('currency', 'VND'),
                    'hourly_rate': info.get('hourly_rate', 0)
                })
            except Exception as e:
                continue

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
            'stats': parking_state.get('stats', {
                'total_parked': 0,
                'total_fee': 0,
                'available_spots': 105
            }),
            'vehicles': vehicles_list,
            'floors': dict(floors),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'stats': {
                'total_parked': 0,
                'total_fee': 0,
                'available_spots': 105
            },
            'vehicles': [],
            'floors': {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@app.route('/')
def index():
    return jsonify({
        'message': 'Parking System WebSocket API Server',
        'endpoints': {
            'websocket': 'ws://192.168.80.102:8000',
            'api_data': '/api/data'
        },
        'status': 'running'
    })

@app.route('/api/data')
def get_data():
    return jsonify(get_dashboard_data())

@app.route('/api/vehicle/<license_plate>')
def get_vehicle(license_plate):
    try:
        if license_plate in parking_state['vehicles']:
            info = parking_state['vehicles'][license_plate]

            return jsonify({
                'license_plate': license_plate,
                'location': info['location'],
                'minutes': info.get('minutes', 0),
                'fee': info.get('fee', 0),
                'customer_name': info.get('customer_name', 'Unknown'),
                'area': info.get('area', 'Unknown'),
                'car_type': info.get('car_type', 'Normal'),
                'floor': info.get('floor', 'Unknown'),
                'entry_timestamp': info.get('entry_timestamp'),
                'current_timestamp': info.get('current_timestamp', info.get('entry_timestamp')),
                'parking_status': info.get('parking_status', 'Unknown'),
                'currency': info.get('currency', 'VND'),
                'hourly_rate': info.get('hourly_rate', 0),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({
                'error': 'Vehicle not found',
                'license_plate': license_plate
            }), 404
    except Exception as e:
        return jsonify({
            'error': str(e),
            'license_plate': license_plate
        }), 500

@app.route('/api/history')
def get_history():
    try:
        if not redis_client:
            return jsonify({
                'error': 'Redis not connected',
                'history': []
            })
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        event_type = request.args.get('type', None)
        
        history_data = redis_client.lrange('parking:history', offset, offset + limit - 1)
        
        history_list = []
        for entry in history_data:
            try:
                item = json.loads(entry)
                if event_type and item.get('event_type') != event_type:
                    continue
                history_list.append(item)
            except:
                continue
        
        return jsonify({
            'history': history_list,
            'total': len(history_list),
            'offset': offset,
            'limit': limit
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'history': []
        })

@socketio.on('connect')
def handle_connect():
    print('✅ Client connected')
    socketio.emit('update', get_dashboard_data())

@socketio.on('disconnect')
def handle_disconnect():
    print('❌ Client disconnected')

if __name__ == '__main__':
    kafka_thread = threading.Thread(target=process_kafka_messages, daemon=True)
    kafka_thread.start()
    
    print("🚀 Starting web server on http://192.168.80.102:8000")
    socketio.run(app, host='0.0.0.0', port=8000, debug=False, allow_unsafe_werkzeug=True)