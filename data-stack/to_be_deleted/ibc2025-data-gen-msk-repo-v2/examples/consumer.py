#!/usr/bin/env python3
"""
Example Kafka Consumer for MSK with IAM Authentication

Prerequisites:
pip install kafka-python aws-msk-iam-sasl-signer-python boto3
"""

import json
import signal
import sys
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

# Configuration
BOOTSTRAP_SERVERS = [
    'b-2.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098',
    'b-1.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098',
    'b-3.simplemskuswest2.zha94f.c6.kafka.us-west-2.amazonaws.com:9098'
]
REGION = 'us-west-2'
# Topics to consume from (can be passed as command line arguments)

class MSKConsumer:
    def __init__(self, topics, consumer_group='msk-consumer-group'):
        """Initialize Kafka consumer with IAM authentication"""
        # Create token provider for IAM auth
        token_provider = MSKAuthTokenProvider(region=REGION)
        
        # Create consumer with SASL/IAM configuration
        self.consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            security_protocol='SASL_SSL',
            sasl_mechanism='OAUTHBEARER',
            sasl_oauth_token_provider=token_provider,
            group_id=consumer_group,
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='latest'  # Start from latest messages
        )
        
        print(f"✅ Consumer initialized for topics: {topics}")
        print(f"📍 Consumer group: {consumer_group}")
        
    def consume(self):
        """Consume messages from Kafka topics"""
        print("\n📨 Waiting for messages... (Press Ctrl+C to stop)\n")
        
        try:
            for message in self.consumer:
                self.process_message(message)
        except KafkaError as e:
            print(f"❌ Kafka error: {e}")
        except KeyboardInterrupt:
            print("\n🛑 Stopping consumer...")
        finally:
            self.close()
    
    def process_message(self, message):
        """Process a single message"""
        topic = message.topic
        partition = message.partition
        offset = message.offset
        key = message.key
        value = message.value
        timestamp = message.timestamp
        
        # Generic message processing
        print(f"📦 [{topic}:{partition}:{offset}]")
        print(f"   Key: {key}")
        print(f"   Value: {json.dumps(value, indent=2)}")
        print(f"   Timestamp: {timestamp}")
        print("-" * 50)
    
    
    def close(self):
        """Close the consumer"""
        self.consumer.close()
        print("✅ Consumer closed successfully")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n🛑 Interrupt received, shutting down...')
    sys.exit(0)

def main():
    """Main function to consume messages"""
    print("🚀 Starting MSK Consumer with IAM Authentication")
    print(f"📍 Region: {REGION}")
    print(f"🔗 Bootstrap Servers: {BOOTSTRAP_SERVERS}")
    
    # Get topics from command line arguments or use default
    import sys
    if len(sys.argv) > 1:
        topics = sys.argv[1:]
    else:
        topics = ['test-topic']  # Default topic
    
    print(f"📚 Topics: {topics}")
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize consumer
    consumer = MSKConsumer(topics)
    
    # Start consuming
    consumer.consume()

if __name__ == "__main__":
    main()