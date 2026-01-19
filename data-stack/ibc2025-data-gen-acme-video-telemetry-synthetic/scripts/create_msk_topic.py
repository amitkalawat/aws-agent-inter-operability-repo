#!/usr/bin/env python3
"""
Standalone script to create MSK topic with IAM authentication
Can be run locally or as a Lambda function
"""

import json
import boto3
import logging
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from kafka.sasl.oauth import AbstractTokenProvider
from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MSK_CLUSTER_ARN = "arn:aws:kafka:eu-central-1:241533163649:cluster/simple-msk-eu-central-1/26147c0d-2edc-4f80-9428-346a44b1659e-2"
TOPIC_NAME = "acme-telemetry"
AWS_REGION = "eu-central-1"

class MSKTokenProvider(AbstractTokenProvider):
    """Token provider for MSK IAM authentication"""
    def __init__(self, region='eu-central-1'):
        self.region = region
    
    def token(self):
        token, _ = MSKAuthTokenProvider.generate_auth_token(self.region)
        return token

def create_topic():
    """Create the acme-telemetry topic in MSK"""
    try:
        # Get bootstrap servers
        msk = boto3.client('kafka', region_name=AWS_REGION)
        response = msk.get_bootstrap_brokers(ClusterArn=MSK_CLUSTER_ARN)
        
        bootstrap_servers = response.get('BootstrapBrokerStringSaslIam')
        logger.info(f"Bootstrap servers: {bootstrap_servers}")
        
        # Create admin client with IAM auth
        tp = MSKTokenProvider(region=AWS_REGION)
        admin = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            security_protocol='SASL_SSL',
            sasl_mechanism='OAUTHBEARER',
            sasl_oauth_token_provider=tp,
            request_timeout_ms=30000,
            api_version_auto_timeout_ms=10000
        )
        
        # Define topic configuration
        new_topic = NewTopic(
            name=TOPIC_NAME,
            num_partitions=20,  # Good for parallelism
            replication_factor=3,  # For high availability
            topic_configs={
                'retention.ms': '604800000',  # 7 days
                'compression.type': 'gzip',
                'min.insync.replicas': '2'  # For durability
            }
        )
        
        # Create the topic
        logger.info(f"Creating topic: {TOPIC_NAME}")
        try:
            fs = admin.create_topics([new_topic], validate_only=False)
            for topic, f in fs.items():
                try:
                    f.result()  # The result itself is None
                    logger.info(f"Topic {topic} created successfully")
                    status = "created"
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.info(f"Topic {topic} already exists")
                        status = "already_exists"
                    else:
                        raise
        except TopicAlreadyExistsError:
            logger.info(f"Topic {TOPIC_NAME} already exists")
            status = "already_exists"
        
        # List all topics to confirm
        all_topics = admin.list_topics()
        logger.info(f"All topics in cluster: {list(all_topics)}")
        
        # Close admin client
        admin.close()
        
        return {
            'success': True,
            'topic': TOPIC_NAME,
            'status': status,
            'all_topics': list(all_topics)
        }
        
    except Exception as e:
        logger.error(f"Error creating topic: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

def lambda_handler(event, context):
    """Lambda handler wrapper"""
    result = create_topic()
    return {
        'statusCode': 200 if result['success'] else 500,
        'body': json.dumps(result)
    }

if __name__ == "__main__":
    # Run directly
    result = create_topic()
    print(json.dumps(result, indent=2))