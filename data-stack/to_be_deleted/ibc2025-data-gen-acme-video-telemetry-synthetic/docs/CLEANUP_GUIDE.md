# ACME Telemetry Pipeline - Cleanup Guide

## Overview

This guide provides instructions for safely removing all components of the ACME Telemetry Pipeline from your AWS account. This includes both manual cleanup using scripts and CDK-based cleanup.

## ⚠️ Warning

**Cleanup operations are DESTRUCTIVE and IRREVERSIBLE**. Once deleted:
- All Lambda functions will be removed
- EventBridge rules will be deleted
- Firehose delivery streams will be terminated
- CloudWatch logs may be deleted
- S3 data can optionally be deleted

Always backup important data before running cleanup operations.

## 📋 Pre-Cleanup Checklist

Before cleaning up, ensure you:
1. ✅ Have backed up any important telemetry data from S3
2. ✅ Have documented any custom configurations
3. ✅ Have informed stakeholders about the cleanup
4. ✅ Have verified you're in the correct AWS account/region
5. ✅ Have necessary permissions to delete resources

## 🔍 List Current Resources

Before cleanup, check what's deployed:

```bash
# List all pipeline resources
./scripts/list_resources.sh

# Check specific resources manually
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'AcmeTelemetry')]"
aws events list-rules --name-prefix "AcmeTelemetry"
aws firehose list-delivery-streams
```

## 🗑️ Cleanup Methods

### Method 1: Automated Script Cleanup (Recommended)

We provide two scripts for resource management:

#### List Resources Script
```bash
# Check what's currently deployed
./scripts/list_resources.sh
```

This shows:
- Lambda function status
- EventBridge rule configuration
- Firehose stream status
- S3 data statistics
- Recent activity metrics

#### Cleanup Script
```bash
# Interactive cleanup (with confirmations)
./scripts/cleanup_pipeline.sh

# Force cleanup (no confirmations - BE CAREFUL!)
./scripts/cleanup_pipeline.sh --force
```

The cleanup script will:
1. Disable EventBridge rules (stops new invocations)
2. Delete EventBridge rules
3. Delete Lambda functions
4. Delete Firehose delivery stream
5. Delete CloudWatch log groups
6. Optionally delete S3 data

### Method 2: CDK Cleanup

If you deployed using CDK:

```bash
cd cdk

# Destroy all stacks
cdk destroy --all

# Or destroy specific stacks
cdk destroy AcmeTelemetry-Monitoring  # Remove monitoring first
cdk destroy AcmeTelemetry-Pipeline    # Then main pipeline
cdk destroy AcmeTelemetry-MSK         # Then MSK (if created)
cdk destroy AcmeTelemetry-Network     # Finally networking (if created)
```

### Method 3: Manual Cleanup

If scripts fail or for selective cleanup:

#### 1. Stop Event Generation
```bash
# Disable EventBridge rule
aws events disable-rule --name AcmeTelemetry-GeneratorSchedule

# Remove rule targets
aws events remove-targets --rule AcmeTelemetry-GeneratorSchedule --ids "1"

# Delete rule
aws events delete-rule --name AcmeTelemetry-GeneratorSchedule
```

#### 2. Delete Lambda Functions
```bash
# Delete Generator
aws lambda delete-function --function-name AcmeTelemetry-Generator

# Delete Producer
aws lambda delete-function --function-name AcmeTelemetry-Producer

# Delete any test functions
aws lambda delete-function --function-name AcmeTelemetry-TopicManager
aws lambda delete-function --function-name AcmeTelemetry-ConnectivityTest
```

#### 3. Delete Firehose
```bash
# Delete delivery stream
aws firehose delete-delivery-stream \
  --delivery-stream-name AcmeTelemetry-MSK-to-S3
```

#### 4. Delete CloudWatch Logs
```bash
# Delete log groups
aws logs delete-log-group --log-group-name /aws/lambda/AcmeTelemetry-Generator
aws logs delete-log-group --log-group-name /aws/lambda/AcmeTelemetry-Producer
aws logs delete-log-group --log-group-name /aws/kinesisfirehose/AcmeTelemetry-MSK-to-S3
```

#### 5. Clean S3 Data (Optional)
```bash
# Delete telemetry data
aws s3 rm s3://acme-telemetry-878687028155-us-west-2/telemetry/ --recursive

# Delete error logs
aws s3 rm s3://acme-telemetry-878687028155-us-west-2/errors/ --recursive
```

## 🔒 Resources NOT Deleted Automatically

The following resources are NOT deleted by cleanup scripts and must be managed separately:

### 1. MSK Cluster
```bash
# MSK clusters are expensive and shared - handle with care!
# Delete only if you're sure it's not used elsewhere

# First, delete the topic
# (Requires Kafka admin tools or custom script)
```

### 2. IAM Roles
```bash
# List roles
aws iam list-roles --query "Roles[?contains(RoleName, 'AcmeTelemetry')]"

# Delete role (first detach policies)
aws iam delete-role --role-name AcmeTelemetry-Generator-Role
aws iam delete-role --role-name AcmeTelemetry-Producer-Role
aws iam delete-role --role-name AcmeTelemetry-Firehose-Role
```

### 3. S3 Bucket
```bash
# The bucket itself is not deleted, only the data
# To delete bucket (must be empty first):
aws s3 rb s3://acme-telemetry-878687028155-us-west-2
```

### 4. VPC and Security Groups
```bash
# Only delete if created specifically for this pipeline
# Check for other resources using them first!
```

## 📊 Cleanup Verification

After cleanup, verify all resources are removed:

```bash
# Check Lambda functions
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'AcmeTelemetry')]" \
  --output table

# Check EventBridge rules
aws events list-rules --name-prefix "AcmeTelemetry" --output table

# Check Firehose streams
aws firehose list-delivery-streams --output json | \
  jq '.DeliveryStreamNames[] | select(contains("AcmeTelemetry"))'

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/AcmeTelemetry" \
  --output table
```

## 🆘 Troubleshooting

### Issue: Resources won't delete

**Cause**: Dependencies or permissions
**Solution**: 
1. Check CloudFormation stacks for dependencies
2. Ensure IAM role has deletion permissions
3. Try force deletion with CLI

### Issue: S3 bucket won't delete

**Cause**: Bucket not empty or versioning enabled
**Solution**:
```bash
# Delete all versions
aws s3api delete-objects --bucket BUCKET_NAME \
  --delete "$(aws s3api list-object-versions --bucket BUCKET_NAME \
  --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

# Then delete bucket
aws s3 rb s3://BUCKET_NAME --force
```

### Issue: Firehose in DELETING state

**Cause**: Normal behavior, can take several minutes
**Solution**: Wait 5-10 minutes for deletion to complete

### Issue: Lambda functions reappear

**Cause**: EventBridge rule still active
**Solution**: Ensure EventBridge rule is deleted first

## 💰 Cost Implications

After cleanup:
- **Immediate**: Lambda and Firehose charges stop
- **Hourly**: No further MSK data transfer charges
- **Daily**: CloudWatch logs ingestion stops
- **Monthly**: S3 storage costs stop (if data deleted)

## 📝 Post-Cleanup Actions

1. **Document**: Record what was deleted and when
2. **Notify**: Inform team members of cleanup completion
3. **Verify**: Check next AWS bill for stopped charges
4. **Archive**: Save any configuration files for future reference

## 🔄 Re-deployment

If you need to redeploy after cleanup:

### Using Scripts:
```bash
./scripts/deploy_lambdas.sh
./scripts/setup_eventbridge.sh
./scripts/create_firehose.sh
```

### Using CDK:
```bash
cd cdk
cdk deploy --all
```

## ⚡ Quick Commands Reference

```bash
# Check what's deployed
./scripts/list_resources.sh

# Interactive cleanup
./scripts/cleanup_pipeline.sh

# Force cleanup (no prompts)
./scripts/cleanup_pipeline.sh --force

# CDK cleanup
cd cdk && cdk destroy --all

# Manual S3 cleanup
aws s3 rm s3://acme-telemetry-878687028155-us-west-2/telemetry/ --recursive
```

## 📞 Support

If you encounter issues during cleanup:
1. Check CloudTrail logs for deletion errors
2. Review IAM permissions
3. Check AWS Service Health Dashboard
4. Contact AWS Support if resources are stuck

---

**Remember**: Always verify you're in the correct AWS account and region before running cleanup commands!