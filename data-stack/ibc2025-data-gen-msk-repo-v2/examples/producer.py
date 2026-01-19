#!/usr/bin/env python3
"""
Example Kafka Producer for MSK with IAM Authentication

Prerequisites:
pip install kafka-python aws-msk-iam-sasl-signer-python boto3
"""

import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

# Configuration
BOOTSTRAP_SERVERS = [
    'b-2.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098',
    'b-1.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098',
    'b-3.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098'
]
REGION = 'us-west-2'

class MSKProducer:
    def __init__(self):
        """Initialize Kafka producer with IAM authentication"""
        # Create token provider for IAM auth
        token_provider = MSKAuthTokenProvider(region=REGION)
        
        # Create producer with SASL/IAM configuration
        self.producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            security_protocol='SASL_SSL',
            sasl_mechanism='OAUTHBEARER',
            sasl_oauth_token_provider=token_provider,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # Wait for all replicas to acknowledge
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        
    def produce_event(self, topic, key, value):
        """Send a message to Kafka topic"""
        try:
            future = self.producer.send(topic, key=key, value=value)
            record_metadata = future.get(timeout=10)
            print(f"✅ Sent to {topic}: partition={record_metadata.partition}, offset={record_metadata.offset}")
            return True
        except KafkaError as e:
            print(f"❌ Error sending to {topic}: {e}")
            return False
    
    def close(self):
        """Flush and close the producer"""
        self.producer.flush()
        self.producer.close()

def generate_sample_event(topic_name):
    """Generate a sample event for a given topic"""
    
    # Generic sample event
    event = {
        'id': f"{topic_name}_{random.randint(10000, 99999)}",
        'type': topic_name,
        'timestamp': datetime.utcnow().isoformat(),
        'data': {
            'value': round(random.uniform(1.0, 100.0), 2),
            'status': random.choice(['active', 'pending', 'completed']),
            'source': random.choice(['api', 'web', 'mobile'])
        },
        'metadata': {
            'host': f"server-{random.randint(1, 10)}",
            'region': REGION,
            'version': '1.0.0'
        }
    }
    
    return event

def main():
    """Main function to produce sample data"""
    print("🚀 Starting MSK Producer with IAM Authentication")
    print(f"📍 Region: {REGION}")
    print(f"🔗 Bootstrap Servers: {BOOTSTRAP_SERVERS}")
    
    # Initialize producer
    producer = MSKProducer()
    
    # Get topic name from user or use default
    import sys
    topic_name = sys.argv[1] if len(sys.argv) > 1 else 'test-topic'
    print(f"📝 Publishing to topic: {topic_name}")
    
    try:
        # Produce messages continuously
        message_count = 0
        while True:
            # Generate sample event
            event = generate_sample_event(topic_name)
            
            # Use event ID as the key for partitioning
            key = event.get('id', None)
            producer.produce_event(topic_name, key, event)
            message_count += 1
            
            print(f"📊 Total messages sent: {message_count}")
            
            # Wait before sending next message
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping producer...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        producer.close()
        print("✅ Producer closed successfully")

if __name__ == "__main__":
    main()