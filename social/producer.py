import time
import random
import json
from datetime import datetime
from enum import Enum
from kafka import KafkaProducer


class EventType(Enum):
    """Social media event types"""
    POST = "post"
    COMMENT = "comment"
    LIKE = "like"
    SHARE = "share"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    VIEW = "view"
    STORY = "story"
    DIRECT_MESSAGE = "direct_message"


class ContentCategory(Enum):
    """Content categories"""
    TECHNOLOGY = "Technology"
    FASHION = "Fashion"
    FOOD = "Food"
    TRAVEL = "Travel"
    FITNESS = "Fitness"
    GAMING = "Gaming"
    MUSIC = "Music"
    ART = "Art"
    SPORTS = "Sports"
    NEWS = "News"
    COMEDY = "Comedy"
    EDUCATION = "Education"


class SentimentType(Enum):
    """Sentiment analysis results"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SocialMediaEvent:
    """Class representing a social media activity event"""

    # Simulated user base
    USERS = [f"user_{i:05d}" for i in range(1, 1001)]  # 1000 users
    
    # Popular hashtags by category
    HASHTAGS = {
        "Technology": ["#tech", "#ai", "#coding", "#innovation", "#startup"],
        "Fashion": ["#fashion", "#style", "#ootd", "#beauty", "#trendy"],
        "Food": ["#foodie", "#cooking", "#recipe", "#yummy", "#instafood"],
        "Travel": ["#travel", "#wanderlust", "#vacation", "#explore", "#adventure"],
        "Fitness": ["#fitness", "#gym", "#workout", "#health", "#motivation"],
        "Gaming": ["#gaming", "#gamer", "#esports", "#twitch", "#gameplay"],
        "Music": ["#music", "#musician", "#concert", "#newmusic", "#spotify"],
        "Art": ["#art", "#artist", "#drawing", "#creative", "#painting"],
        "Sports": ["#sports", "#athlete", "#fitness", "#training", "#competition"],
        "News": ["#news", "#breaking", "#today", "#update", "#world"],
        "Comedy": ["#funny", "#memes", "#lol", "#humor", "#comedy"],
        "Education": ["#learning", "#education", "#knowledge", "#study", "#tutorial"]
    }
    
    POST_TEMPLATES = [
        "Just discovered something amazing about {}!",
        "Can't get enough of {} lately 🔥",
        "Here's my take on the latest {} trend...",
        "Absolutely loving this {} experience!",
        "Check out my new {} creation!",
        "This {} moment made my day!",
        "Sharing some {} inspiration with you all",
        "My {} journey continues...",
        "Excited to announce my latest {} project!",
        "Behind the scenes of my {} work"
    ]
    
    COMMENT_TEMPLATES = [
        "This is amazing! 🔥",
        "Love this!",
        "Great content!",
        "Thanks for sharing!",
        "So inspiring!",
        "Can't wait to see more!",
        "This is exactly what I needed!",
        "Incredible work!",
        "You're killing it! 💪",
        "Keep it up!"
    ]

    LOCATIONS = [
        "New York, NY", "Los Angeles, CA", "London, UK", "Tokyo, Japan",
        "Paris, France", "Sydney, Australia", "Mumbai, India", "Toronto, Canada",
        "Dubai, UAE", "Singapore", "Berlin, Germany", "São Paulo, Brazil",
        "Seoul, South Korea", "Mexico City, Mexico", "Madrid, Spain",
        "Amsterdam, Netherlands", "Bangkok, Thailand", "Istanbul, Turkey",
        "Hong Kong", "Miami, FL"
    ]

    DEVICES = ["iOS", "Android", "Web", "Desktop"]

    def __init__(self, existing_posts=None, event_id_counter=1):
        self.event_id = f"EVT{event_id_counter:010d}"
        self.event_type = random.choice(list(EventType))
        self.user_id = random.choice(self.USERS)
        self.timestamp = int(time.time())
        
        # Content-related fields
        self.category = random.choice(list(ContentCategory))
        self.hashtags = random.sample(self.HASHTAGS[self.category.value], 
                                     random.randint(1, 3))
        
        # Engagement metrics
        self.like_count = 0
        self.comment_count = 0
        self.share_count = 0
        self.view_count = 0
        
        # Additional context
        self.location = random.choice(self.LOCATIONS) if random.random() > 0.3 else None
        self.device = random.choice(self.DEVICES)
        self.sentiment = random.choice(list(SentimentType))
        
        # Event-specific fields
        if self.event_type == EventType.POST:
            self.content = random.choice(self.POST_TEMPLATES).format(
                self.category.value.lower()
            )
            self.post_id = f"POST{event_id_counter:010d}"
            self.has_image = random.random() > 0.4
            self.has_video = random.random() > 0.7
            self.is_sponsored = random.random() > 0.9
            
        elif self.event_type == EventType.COMMENT:
            if existing_posts:
                self.parent_post_id = random.choice(list(existing_posts.keys()))
                self.parent_user_id = existing_posts[self.parent_post_id]
            else:
                self.parent_post_id = f"POST{random.randint(1, max(1, event_id_counter-1)):010d}"
                self.parent_user_id = random.choice(self.USERS)
            self.content = random.choice(self.COMMENT_TEMPLATES)
            self.comment_id = f"CMT{event_id_counter:010d}"
            
        elif self.event_type == EventType.LIKE:
            if existing_posts:
                self.target_post_id = random.choice(list(existing_posts.keys()))
                self.target_user_id = existing_posts[self.target_post_id]
            else:
                self.target_post_id = f"POST{random.randint(1, max(1, event_id_counter-1)):010d}"
                self.target_user_id = random.choice(self.USERS)
                
        elif self.event_type == EventType.SHARE:
            if existing_posts:
                self.shared_post_id = random.choice(list(existing_posts.keys()))
                self.original_user_id = existing_posts[self.shared_post_id]
            else:
                self.shared_post_id = f"POST{random.randint(1, max(1, event_id_counter-1)):010d}"
                self.original_user_id = random.choice(self.USERS)
            self.share_comment = random.choice([
                "Must see this!",
                "Check this out!",
                "Thought you'd like this",
                None
            ])
            
        elif self.event_type == EventType.FOLLOW:
            self.target_user_id = random.choice([u for u in self.USERS if u != self.user_id])
            
        elif self.event_type == EventType.UNFOLLOW:
            self.target_user_id = random.choice([u for u in self.USERS if u != self.user_id])
            
        elif self.event_type == EventType.VIEW:
            if existing_posts:
                self.viewed_post_id = random.choice(list(existing_posts.keys()))
                self.viewed_user_id = existing_posts[self.viewed_post_id]
            else:
                self.viewed_post_id = f"POST{random.randint(1, max(1, event_id_counter-1)):010d}"
                self.viewed_user_id = random.choice(self.USERS)
            self.view_duration_seconds = random.randint(1, 120)
            self.scroll_depth_percent = random.randint(10, 100)
            
        elif self.event_type == EventType.STORY:
            self.story_id = f"STORY{event_id_counter:010d}"
            self.expires_in_hours = 24
            self.has_image = random.random() > 0.3
            self.has_video = random.random() > 0.6
            
        elif self.event_type == EventType.DIRECT_MESSAGE:
            self.recipient_user_id = random.choice([u for u in self.USERS if u != self.user_id])
            self.message_length = random.randint(10, 500)
            self.has_attachment = random.random() > 0.7

    def get_event_info(self):
        """Return event information as a dictionary"""
        event = {
            "event_id": self.event_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_unix": self.timestamp,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "category": self.category.value,
            "hashtags": self.hashtags,
            "location": self.location,
            "device": self.device,
            "sentiment": self.sentiment.value
        }
        
        # Add event-specific fields
        if self.event_type == EventType.POST:
            event.update({
                "post_id": self.post_id,
                "content": self.content,
                "has_image": self.has_image,
                "has_video": self.has_video,
                "is_sponsored": self.is_sponsored,
                "engagement": {
                    "likes": self.like_count,
                    "comments": self.comment_count,
                    "shares": self.share_count,
                    "views": self.view_count
                }
            })
            
        elif self.event_type == EventType.COMMENT:
            event.update({
                "comment_id": self.comment_id,
                "parent_post_id": self.parent_post_id,
                "parent_user_id": self.parent_user_id,
                "content": self.content
            })
            
        elif self.event_type == EventType.LIKE:
            event.update({
                "target_post_id": self.target_post_id,
                "target_user_id": self.target_user_id
            })
            
        elif self.event_type == EventType.SHARE:
            event.update({
                "shared_post_id": self.shared_post_id,
                "original_user_id": self.original_user_id,
                "share_comment": self.share_comment
            })
            
        elif self.event_type == EventType.FOLLOW:
            event.update({
                "target_user_id": self.target_user_id
            })
            
        elif self.event_type == EventType.UNFOLLOW:
            event.update({
                "target_user_id": self.target_user_id
            })
            
        elif self.event_type == EventType.VIEW:
            event.update({
                "viewed_post_id": self.viewed_post_id,
                "viewed_user_id": self.viewed_user_id,
                "view_duration_seconds": self.view_duration_seconds,
                "scroll_depth_percent": self.scroll_depth_percent
            })
            
        elif self.event_type == EventType.STORY:
            event.update({
                "story_id": self.story_id,
                "expires_in_hours": self.expires_in_hours,
                "has_image": self.has_image,
                "has_video": self.has_video
            })
            
        elif self.event_type == EventType.DIRECT_MESSAGE:
            event.update({
                "recipient_user_id": self.recipient_user_id,
                "message_length": self.message_length,
                "has_attachment": self.has_attachment
            })
        
        return event


def social_media_stream_to_kafka(
    kafka_bootstrap_servers,
    kafka_topic,
    duration_minutes=30,
    events_per_second=10
):
    """
    Stream social media activity events to Kafka
    
    Args:
        kafka_bootstrap_servers: Kafka server address
        kafka_topic: Topic name to publish events
        duration_minutes: How long to run the stream
        events_per_second: Target number of events per second
    """
    
    # Initialize Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    event_interval = 1.0 / events_per_second

    # Track existing posts for realistic interactions
    existing_posts = {}  # post_id -> user_id
    event_id_counter = 1
    
    # Statistics
    event_counts = {event_type: 0 for event_type in EventType}
    total_events = 0

    try:
        print(f"Starting Social Media Activity Stream to Kafka topic: {kafka_topic}")
        print(f"Kafka server: {kafka_bootstrap_servers}")
        print(f"Target rate: {events_per_second} events/second")
        print("-" * 90)

        while time.time() < end_time:
            # Create new event
            event = SocialMediaEvent(existing_posts, event_id_counter)
            
            # Track posts for realistic interactions
            if event.event_type == EventType.POST:
                existing_posts[event.post_id] = event.user_id
                # Limit tracking to recent 1000 posts
                if len(existing_posts) > 1000:
                    oldest_post = list(existing_posts.keys())[0]
                    del existing_posts[oldest_post]
            
            # Get event info
            event_data = event.get_event_info()
            
            # Send to Kafka (key = user_id for partitioning)
            producer.send(
                kafka_topic,
                key=event_data['user_id'],
                value=event_data
            )
            
            # Update statistics
            event_counts[event.event_type] += 1
            total_events += 1
            
            # Print to console (simplified view)
            if total_events % 50 == 0:  # Print summary every 50 events
                elapsed = time.time() - start_time
                rate = total_events / elapsed if elapsed > 0 else 0
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Events: {total_events} | "
                      f"Rate: {rate:.1f}/s | Active Posts: {len(existing_posts)}")
                print(f"Distribution: ", end="")
                for event_type, count in event_counts.items():
                    if count > 0:
                        print(f"{event_type.value}={count} ", end="")
                print()
            else:
                # Print individual event
                print(f"{event_data['timestamp']} | {event_data['event_type']:12} | "
                      f"User: {event_data['user_id']:10} | "
                      f"Category: {event_data['category']:12} | "
                      f"Device: {event_data['device']}")
            
            event_id_counter += 1
            
            # Sleep to maintain target rate
            time.sleep(event_interval)

    except KeyboardInterrupt:
        print("\n\nStopping stream...")
    finally:
        producer.flush()
        producer.close()
        
        elapsed = time.time() - start_time
        print(f"\n{'='*90}")
        print(f"Stream Summary:")
        print(f"{'='*90}")
        print(f"Total Events Generated: {total_events}")
        print(f"Duration: {elapsed:.2f} seconds")
        print(f"Average Rate: {total_events/elapsed:.2f} events/second")
        print(f"\nEvent Type Distribution:")
        for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_events * 100) if total_events > 0 else 0
            print(f"  {event_type.value:20} : {count:6} ({percentage:.1f}%)")
        print(f"\nKafka Producer closed")


if __name__ == "__main__":
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS = '192.168.1.56:9092'
    KAFKA_TOPIC = 'social-media-events'

    # Stream for 30 minutes with 10 events per second
    # This simulates ~18,000 events in 30 minutes
    social_media_stream_to_kafka(
        kafka_bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        kafka_topic=KAFKA_TOPIC,
        duration_minutes=30,
        events_per_second=10
    )