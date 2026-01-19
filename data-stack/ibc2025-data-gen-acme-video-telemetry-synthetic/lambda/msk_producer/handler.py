import json
import boto3
import os
import logging
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError
from kafka.sasl.oauth import AbstractTokenProvider
import time
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration from environment variables
MSK_CLUSTER_ARN = os.environ.get('MSK_CLUSTER_ARN')
TOPIC_NAME = os.environ.get('TOPIC_NAME', 'acme-telemetry')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-central-1')

# MSK client
msk_client = boto3.client('kafka', region_name=AWS_REGION)

class MSKTokenProvider(AbstractTokenProvider):
    """Token provider for MSK IAM authentication"""
    def __init__(self, region='eu-central-1'):
        self.region = region
    
    def token(self):
        """Generate authentication token"""
        token, _ = MSKAuthTokenProvider.generate_auth_token(self.region)
        return token

def get_bootstrap_servers():
    """Get MSK bootstrap servers"""
    try:
        response = msk_client.get_bootstrap_brokers(
            ClusterArn=MSK_CLUSTER_ARN
        )
        
        # Use IAM authentication endpoint
        bootstrap_servers = response.get('BootstrapBrokerStringSaslIam')
        
        if not bootstrap_servers:
            raise ValueError("No IAM bootstrap servers found")
            
        logger.info(f"Bootstrap servers: {bootstrap_servers}")
        return bootstrap_servers
        
    except Exception as e:
        logger.error(f"Error getting bootstrap servers: {str(e)}")
        raise

def ensure_topic_exists(bootstrap_servers):
    """Ensure the topic exists, create if not"""
    logger.info(f"Checking if topic {TOPIC_NAME} exists...")
    
    try:
        # Create admin client
        tp = MSKTokenProvider(region=AWS_REGION)
        admin = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            security_protocol='SASL_SSL',
            sasl_mechanism='OAUTHBEARER',
            sasl_oauth_token_provider=tp,
            request_timeout_ms=30000,
            api_version_auto_timeout_ms=10000
        )
        
        # Check if topic exists
        existing_topics = admin.list_topics()
        if TOPIC_NAME in existing_topics:
            logger.info(f"Topic {TOPIC_NAME} already exists")
            admin.close()
            return True
        
        # Create topic if it doesn't exist
        logger.info(f"Creating topic {TOPIC_NAME}...")
        new_topic = NewTopic(
            name=TOPIC_NAME,
            num_partitions=20,
            replication_factor=3,
            topic_configs={
                'retention.ms': '604800000',  # 7 days
                'compression.type': 'gzip',
                'min.insync.replicas': '2'
            }
        )
        
        try:
            fs = admin.create_topics([new_topic], validate_only=False)
            for topic, f in fs.items():
                f.result()  # Wait for completion
                logger.info(f"Topic {topic} created successfully")
        except TopicAlreadyExistsError:
            logger.info(f"Topic {TOPIC_NAME} already exists")
        
        admin.close()
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring topic exists: {str(e)}")
        return False

def create_producer(bootstrap_servers):
    """Create Kafka producer with IAM authentication"""
    logger.info("Configuring IAM authentication for MSK")
    
    # Create token provider
    tp = MSKTokenProvider(region=AWS_REGION)
    
    # Producer configuration
    conf = {
        'bootstrap_servers': bootstrap_servers,
        'security_protocol': 'SASL_SSL',
        'sasl_mechanism': 'OAUTHBEARER',
        'sasl_oauth_token_provider': tp,
        'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
        'key_serializer': lambda v: v.encode('utf-8') if v else None,
        'acks': 'all',
        'retries': 3,
        'max_in_flight_requests_per_connection': 5,
        'compression_type': 'gzip',
        'batch_size': 16384,
        'linger_ms': 100,
        'buffer_memory': 33554432,
        'request_timeout_ms': 30000,
        'api_version_auto_timeout_ms': 10000
    }
    
    return KafkaProducer(**conf)

def send_events_to_kafka(producer, events, batch_id):
    """Send events to Kafka topic"""
    success_count = 0
    error_count = 0
    errors = []
    
    # Send each event
    for event in events:
        try:
            # Use customer_id as key for partitioning
            key = event.get('customer_id', '')
            
            # Send to Kafka
            future = producer.send(
                TOPIC_NAME,
                key=key,
                value=event
            )
            
            # Optionally wait for confirmation (can be removed for better performance)
            # future.get(timeout=10)
            
            success_count += 1
            
        except KafkaError as e:
            error_count += 1
            errors.append(str(e))
            logger.error(f"Error sending event: {str(e)}")
        except Exception as e:
            error_count += 1
            errors.append(str(e))
            logger.error(f"Unexpected error: {str(e)}")
    
    # Flush and wait for any pending messages
    logger.info("Waiting for messages to be delivered...")
    producer.flush(timeout=10)
    
    return success_count, error_count, errors

def lambda_handler(event, context):
    """Main Lambda handler"""
    producer = None
    start_time = time.time()
    
    try:
        # Extract events from payload
        events = event.get('events', [])
        batch_id = event.get('batch_id', 'unknown')
        batch_number = event.get('batch_number', 0)
        
        logger.info(f"Received payload with batch_id: {batch_id}")
        logger.info(f"Processing {len(events)} events")
        
        if not events:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No events provided'
                })
            }
        
        # Get bootstrap servers
        logger.info("Initializing Kafka producer...")
        bootstrap_servers = get_bootstrap_servers()
        
        # Ensure topic exists
        ensure_topic_exists(bootstrap_servers)
        
        # Create producer
        producer = create_producer(bootstrap_servers)
        logger.info("Kafka producer initialized successfully")
        
        # Send events to Kafka
        success_count, error_count, errors = send_events_to_kafka(
            producer, 
            events, 
            batch_id
        )
        
        # Calculate metrics
        processing_time = time.time() - start_time
        events_per_second = len(events) / processing_time if processing_time > 0 else 0
        
        logger.info(f"Successfully sent {success_count}/{len(events)} events in {processing_time:.2f}s ({events_per_second:.2f} events/sec)")
        
        # Publish CloudWatch metrics
        try:
            cloudwatch = boto3.client('cloudwatch')
            cloudwatch.put_metric_data(
                Namespace='AcmeTelemetry',
                MetricData=[
                    {
                        'MetricName': 'EventsSent',
                        'Value': success_count,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'EventErrors',
                        'Value': error_count,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'ProcessingTime',
                        'Value': processing_time,
                        'Unit': 'Seconds'
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Error publishing metrics: {str(e)}")
        
        # Return response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Events published successfully',
                'batch_id': batch_id,
                'batch_number': batch_number,
                'events_processed': len(events),
                'success_count': success_count,
                'error_count': error_count,
                'processing_time': processing_time,
                'events_per_second': events_per_second,
                'errors': errors[:10] if errors else []  # Return first 10 errors
            })
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in MSK producer: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'batch_id': event.get('batch_id', 'unknown')
            })
        }
        
    finally:
        # Close producer if it was created
        if producer:
            try:
                producer.close(timeout=5)
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing producer: {str(e)}")