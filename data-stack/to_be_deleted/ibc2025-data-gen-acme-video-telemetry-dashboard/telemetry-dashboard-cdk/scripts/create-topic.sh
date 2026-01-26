#!/bin/bash

# Get MSK cluster details
CLUSTER_ARN="arn:aws:kafka:eu-central-1:241533163649:cluster/simple-msk-eu-central-1/26147c0d-2edc-4f80-9428-346a44b1659e-2"
REGION="eu-central-1"

echo "Getting MSK bootstrap brokers..."
BOOTSTRAP_BROKERS=$(aws kafka get-bootstrap-brokers --cluster-arn $CLUSTER_ARN --region $REGION --query 'BootstrapBrokerStringSaslIam' --output text)
echo "Bootstrap brokers: $BOOTSTRAP_BROKERS"

# Install kafka client tools if not present
if ! command -v kafka-topics &> /dev/null; then
    echo "Installing Kafka client tools..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install kafka
    else
        echo "Please install Kafka client tools manually"
        exit 1
    fi
fi

# Create the topic using IAM authentication
echo "Creating topic 'acme-telemetry'..."
kafka-topics --bootstrap-server $BOOTSTRAP_BROKERS \
    --command-config /tmp/kafka-client.properties \
    --create \
    --topic acme-telemetry \
    --partitions 3 \
    --replication-factor 3 \
    --if-not-exists

echo "Listing topics..."
kafka-topics --bootstrap-server $BOOTSTRAP_BROKERS \
    --command-config /tmp/kafka-client.properties \
    --list