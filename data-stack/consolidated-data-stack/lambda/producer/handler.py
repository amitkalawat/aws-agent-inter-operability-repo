import json
import os
from typing import Any

from aws_msk_iam_sasl_signer import MSKAuthTokenProvider
from kafka import KafkaProducer
from kafka.sasl.oauth import AbstractTokenProvider


class MSKTokenProvider(AbstractTokenProvider):
    """Token provider for MSK IAM authentication."""

    def token(self):
        token, _ = MSKAuthTokenProvider.generate_auth_token(os.environ['AWS_REGION'])
        return token


def get_kafka_producer() -> KafkaProducer:
    """Create Kafka producer with IAM authentication."""
    bootstrap_servers = os.environ['BOOTSTRAP_SERVERS']

    return KafkaProducer(
        bootstrap_servers=bootstrap_servers.split(','),
        security_protocol='SASL_SSL',
        sasl_mechanism='OAUTHBEARER',
        sasl_oauth_token_provider=MSKTokenProvider(),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3,
    )


producer = None


def handler(event: dict, context: Any) -> dict:
    """Lambda handler - produces events to MSK."""
    global producer

    if producer is None:
        producer = get_kafka_producer()

    topic = os.environ.get('KAFKA_TOPIC', 'acme-telemetry')
    events = event.get('events', [])

    for evt in events:
        producer.send(topic, value=evt)

    producer.flush()

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Produced {len(events)} events to {topic}',
        }),
    }
