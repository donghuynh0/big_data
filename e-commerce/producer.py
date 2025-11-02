import time
import random
import json
from datetime import datetime
from enum import Enum
from kafka import KafkaProducer


class OrderStatus(Enum):
    """Order processing statuses"""
    CREATED = "Order Created"
    PAYMENT_PENDING = "Payment Pending"
    PAYMENT_CONFIRMED = "Payment Confirmed"
    PREPARING = "Preparing Items"
    READY_TO_SHIP = "Ready to Ship"
    SHIPPED = "Shipped"
    IN_TRANSIT = "In Transit"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class PaymentMethod(Enum):
    """Payment methods"""
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    PAYPAL = "PayPal"
    BANK_TRANSFER = "Bank Transfer"
    COD = "Cash on Delivery"
    WALLET = "Digital Wallet"


class OrderEvent:
    """Class representing an e-commerce order event"""

    PRODUCTS = [
        {"id": "PROD001", "name": "Wireless Headphones", "category": "Electronics", "price": 79.99},
        {"id": "PROD002", "name": "Smart Watch", "category": "Electronics", "price": 199.99},
        {"id": "PROD003", "name": "Running Shoes", "category": "Sports", "price": 89.99},
        {"id": "PROD004", "name": "Yoga Mat", "category": "Sports", "price": 29.99},
        {"id": "PROD005", "name": "Coffee Maker", "category": "Home", "price": 149.99},
        {"id": "PROD006", "name": "Blender", "category": "Home", "price": 69.99},
        {"id": "PROD007", "name": "Winter Jacket", "category": "Fashion", "price": 129.99},
        {"id": "PROD008", "name": "Jeans", "category": "Fashion", "price": 59.99},
        {"id": "PROD009", "name": "Laptop Bag", "category": "Accessories", "price": 39.99},
        {"id": "PROD010", "name": "Phone Case", "category": "Accessories", "price": 19.99},
        {"id": "PROD011", "name": "Bluetooth Speaker", "category": "Electronics", "price": 49.99},
        {"id": "PROD012", "name": "Gaming Mouse", "category": "Electronics", "price": 54.99},
        {"id": "PROD013", "name": "Desk Lamp", "category": "Home", "price": 34.99},
        {"id": "PROD014", "name": "Backpack", "category": "Accessories", "price": 44.99},
        {"id": "PROD015", "name": "Sunglasses", "category": "Fashion", "price": 89.99},
    ]

    CITIES = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
        "San Francisco", "Indianapolis", "Seattle", "Denver", "Boston"
    ]

    WAREHOUSES = ["WH-EAST-01", "WH-WEST-01", "WH-CENTRAL-01", "WH-SOUTH-01", "WH-NORTH-01"]

    def __init__(self, order_id_counter):
        self.order_id = f"ORD{order_id_counter:08d}"
        self.customer_id = f"CUST{random.randint(10000, 99999)}"
        
        # Generate order items (1-5 products)
        num_items = random.randint(1, 5)
        self.items = random.sample(self.PRODUCTS, num_items)
        self.quantities = [random.randint(1, 3) for _ in range(num_items)]
        
        # Calculate order value
        self.subtotal = sum(item["price"] * qty for item, qty in zip(self.items, self.quantities))
        self.tax = round(self.subtotal * 0.08, 2)
        self.shipping = 0 if self.subtotal > 100 else 9.99
        self.total = round(self.subtotal + self.tax + self.shipping, 2)
        
        self.payment_method = random.choice(list(PaymentMethod))
        self.shipping_city = random.choice(self.CITIES)
        self.warehouse = random.choice(self.WAREHOUSES)
        
        self.status = OrderStatus.CREATED
        self.status_duration = 0
        self.status_count = 0
        self.created_timestamp = int(time.time())
        
        # Determine if order will be cancelled (10% chance)
        self.will_cancel = random.random() < 0.1
        self.cancel_at_status = random.choice([
            OrderStatus.PAYMENT_PENDING,
            OrderStatus.PREPARING,
            OrderStatus.READY_TO_SHIP
        ]) if self.will_cancel else None

    def next_status(self):
        """Transition to the next logical order status"""
        self.status_count += 1
        
        # Check if order should be cancelled
        if self.will_cancel and self.status == self.cancel_at_status:
            self.status = OrderStatus.CANCELLED
            return True  # Order complete (cancelled)
        
        # Normal status progression
        if self.status == OrderStatus.CREATED:
            self.status = OrderStatus.PAYMENT_PENDING
            self.status_duration = random.randint(2, 8)
            self.status_count = 0
            
        elif self.status == OrderStatus.PAYMENT_PENDING:
            if self.status_count >= self.status_duration:
                self.status = OrderStatus.PAYMENT_CONFIRMED
                self.status_duration = random.randint(1, 3)
                self.status_count = 0
                
        elif self.status == OrderStatus.PAYMENT_CONFIRMED:
            if self.status_count >= self.status_duration:
                self.status = OrderStatus.PREPARING
                self.status_duration = random.randint(3, 10)
                self.status_count = 0
                
        elif self.status == OrderStatus.PREPARING:
            if self.status_count >= self.status_duration:
                self.status = OrderStatus.READY_TO_SHIP
                self.status_duration = random.randint(1, 4)
                self.status_count = 0
                
        elif self.status == OrderStatus.READY_TO_SHIP:
            if self.status_count >= self.status_duration:
                self.status = OrderStatus.SHIPPED
                self.status_duration = random.randint(2, 5)
                self.status_count = 0
                
        elif self.status == OrderStatus.SHIPPED:
            if self.status_count >= self.status_duration:
                self.status = OrderStatus.IN_TRANSIT
                self.status_duration = random.randint(5, 15)
                self.status_count = 0
                
        elif self.status == OrderStatus.IN_TRANSIT:
            if self.status_count >= self.status_duration:
                self.status = OrderStatus.OUT_FOR_DELIVERY
                self.status_duration = random.randint(2, 6)
                self.status_count = 0
                
        elif self.status == OrderStatus.OUT_FOR_DELIVERY:
            if self.status_count >= self.status_duration:
                self.status = OrderStatus.DELIVERED
                return True  # Order complete (delivered)
                
        elif self.status == OrderStatus.CANCELLED:
            return True  # Order complete (cancelled)
        
        elif self.status == OrderStatus.DELIVERED:
            return True  # Order complete (delivered)
        
        return False  # Order still in progress

    def get_event_info(self):
        """Return event information as a dictionary"""
        current_timestamp = int(time.time())
        processing_time = current_timestamp - self.created_timestamp
        
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_unix": current_timestamp,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "status": self.status.value,
            "status_code": self.status.name,
            "items": [
                {
                    "product_id": item["id"],
                    "product_name": item["name"],
                    "category": item["category"],
                    "price": item["price"],
                    "quantity": qty
                }
                for item, qty in zip(self.items, self.quantities)
            ],
            "order_value": {
                "subtotal": self.subtotal,
                "tax": self.tax,
                "shipping": self.shipping,
                "total": self.total
            },
            "payment_method": self.payment_method.value,
            "shipping_city": self.shipping_city,
            "warehouse": self.warehouse,
            "created_timestamp": self.created_timestamp,
            "processing_time_seconds": processing_time
        }
        
        return event


def ecommerce_stream_to_kafka(
    kafka_bootstrap_servers,
    kafka_topic,
    duration_minutes=30,
    event_interval=2
):
    """
    Stream e-commerce order events to Kafka
    
    Args:
        kafka_bootstrap_servers: Kafka server address
        kafka_topic: Topic name to publish events
        duration_minutes: How long to run the stream
        event_interval: Base interval between events in seconds
    """
    
    # Initialize Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    # Track active orders
    active_orders = []
    order_id_counter = 1
    
    # Create some initial orders
    for _ in range(3):
        order = OrderEvent(order_id_counter)
        active_orders.append(order)
        order_id_counter += 1

    try:
        print(f"Starting E-commerce Order Stream to Kafka topic: {kafka_topic}")
        print(f"Kafka server: {kafka_bootstrap_servers}")
        print("-" * 80)

        while time.time() < end_time:
            # Randomly pick an order to update
            if active_orders:
                order = random.choice(active_orders)
                
                # Get event info
                event_data = order.get_event_info()
                
                # Send to Kafka (key = order_id)
                producer.send(
                    kafka_topic,
                    key=event_data['order_id'],
                    value=event_data
                )
                
                # Print to console (simplified view)
                print(f"{event_data['timestamp']} | Order: {event_data['order_id']} | "
                      f"Customer: {event_data['customer_id']} | "
                      f"Status: {event_data['status']} | "
                      f"Total: ${event_data['order_value']['total']:.2f}")
                
                # Move to next status
                is_complete = order.next_status()
                
                # Remove completed orders
                if is_complete:
                    active_orders.remove(order)
                    print(f"  → Order {order.order_id} completed with status: {order.status.value}")
            
            # Add new orders randomly (simulating new customers)
            if random.random() > 0.5 and len(active_orders) < 30:
                new_order = OrderEvent(order_id_counter)
                active_orders.append(new_order)
                order_id_counter += 1
            
            # Ensure minimum active orders
            while len(active_orders) < 5:
                new_order = OrderEvent(order_id_counter)
                active_orders.append(new_order)
                order_id_counter += 1
            
            # Random delay between events
            delay = random.uniform(event_interval * 0.5, event_interval * 1.5)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\nStopping stream...")
    finally:
        producer.flush()
        producer.close()
        print(f"\nKafka Producer closed")
        print(f"Total orders created: {order_id_counter - 1}")
        print(f"Active orders remaining: {len(active_orders)}")


if __name__ == "__main__":
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS = '192.168.1.56:9092'
    KAFKA_TOPIC = 'ecommerce-orders'

    # Stream for 30 minutes with 2s intervals
    ecommerce_stream_to_kafka(
        kafka_bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        kafka_topic=KAFKA_TOPIC,
        duration_minutes=30,
        event_interval=2
    )