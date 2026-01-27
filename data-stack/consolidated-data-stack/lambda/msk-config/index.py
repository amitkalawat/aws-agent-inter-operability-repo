"""
Custom resource handler for idempotent MSK configuration creation.
Handles the case where configuration already exists.

Note: This is used with CDK cr.Provider, so we return data directly
instead of using cfnresponse.
"""
import json
import boto3

kafka = boto3.client('kafka')


def handler(event, context):
    """Handle CloudFormation custom resource events."""
    print(f"Event: {json.dumps(event)}")

    request_type = event['RequestType']
    props = event['ResourceProperties']

    config_name = props['ConfigurationName']
    kafka_versions = props['KafkaVersions']
    server_properties = props['ServerProperties']

    if request_type in ['Create', 'Update']:
        # Check if configuration already exists
        config_arn = find_configuration_by_name(config_name)

        if config_arn:
            print(f"Configuration '{config_name}' already exists: {config_arn}")
        else:
            print(f"Creating configuration '{config_name}'")
            config_arn = create_configuration(config_name, kafka_versions, server_properties)
            print(f"Created configuration: {config_arn}")

        # Return data for cr.Provider
        return {
            'PhysicalResourceId': config_arn,
            'Data': {
                'Arn': config_arn,
                'Revision': '1',
            }
        }

    elif request_type == 'Delete':
        # MSK configurations can't be deleted if in use, so just succeed
        print(f"Delete requested for configuration '{config_name}' - skipping (MSK configs persist)")
        return {
            'PhysicalResourceId': event.get('PhysicalResourceId', config_name),
        }

    return {}


def find_configuration_by_name(name: str) -> str | None:
    """Find an MSK configuration by name, return its ARN or None."""
    paginator = kafka.get_paginator('list_configurations')

    for page in paginator.paginate():
        for config in page.get('Configurations', []):
            if config['Name'] == name:
                return config['Arn']

    return None


def create_configuration(name: str, kafka_versions: list, server_properties: str) -> str:
    """Create a new MSK configuration and return its ARN."""
    response = kafka.create_configuration(
        Name=name,
        KafkaVersions=kafka_versions,
        ServerProperties=server_properties.encode('utf-8'),
    )
    return response['Arn']
