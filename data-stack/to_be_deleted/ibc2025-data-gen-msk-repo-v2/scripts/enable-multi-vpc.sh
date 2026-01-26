#!/bin/bash

# Enable Multi-VPC connectivity for MSK cluster
# This enables private connectivity for AWS services and cross-VPC access

CLUSTER_ARN="arn:aws:kafka:eu-central-1:241533163649:cluster/simple-msk-eu-central-1/26147c0d-2edc-4f80-9428-346a44b1659e-2"
REGION="eu-central-1"

echo "Checking MSK cluster state..."
STATE=$(aws kafka describe-cluster --cluster-arn $CLUSTER_ARN --region $REGION --query 'ClusterInfo.State' --output text)

if [ "$STATE" != "ACTIVE" ]; then
    echo "❌ Cluster is not ACTIVE. Current state: $STATE"
    echo "Please wait for the cluster to become ACTIVE before enabling Multi-VPC connectivity."
    exit 1
fi

echo "✅ Cluster is ACTIVE"

# Get current version
CURRENT_VERSION=$(aws kafka describe-cluster --cluster-arn $CLUSTER_ARN --region $REGION --query 'ClusterInfo.CurrentVersion' --output text)
echo "Current cluster version: $CURRENT_VERSION"

# Enable Multi-VPC connectivity
echo "Enabling Multi-VPC connectivity with IAM authentication..."
aws kafka update-connectivity \
    --cluster-arn $CLUSTER_ARN \
    --current-version $CURRENT_VERSION \
    --connectivity-info '{"VpcConnectivity":{"ClientAuthentication":{"Sasl":{"Iam":{"Enabled":true}}}}}' \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ Multi-VPC connectivity update initiated successfully"
    echo ""
    echo "Monitoring update progress..."
    
    # Monitor the update
    while true; do
        OPERATION_STATE=$(aws kafka list-cluster-operations \
            --cluster-arn $CLUSTER_ARN \
            --region $REGION \
            --query "ClusterOperationInfoList[0].OperationState" \
            --output text)
        
        echo "$(date '+%H:%M:%S'): Update status: $OPERATION_STATE"
        
        if [ "$OPERATION_STATE" == "UPDATE_COMPLETE" ]; then
            echo "✅ Multi-VPC connectivity enabled successfully!"
            break
        elif [ "$OPERATION_STATE" == "UPDATE_FAILED" ]; then
            echo "❌ Update failed!"
            exit 1
        fi
        
        sleep 10
    done
else
    echo "❌ Failed to initiate Multi-VPC connectivity update"
    exit 1
fi

echo ""
echo "Next steps:"
echo "1. Configure producer applications with IAM authentication"
echo "2. Start producing data to the MSK cluster"