"""
ACME Telemetry Pipeline - Monitoring Stack
CloudWatch dashboards and alarms for the telemetry pipeline
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_lambda as lambda_,
    CfnOutput
)
from constructs import Construct

class MonitoringStack(Stack):
    """Monitoring stack for ACME telemetry pipeline"""
    
    def __init__(self, scope: Construct, construct_id: str,
                 generator_function: lambda_.IFunction,
                 producer_function: lambda_.IFunction,
                 alert_email: str = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # SNS Topic for alerts
        self.alert_topic = sns.Topic(
            self, "AlertTopic",
            display_name="ACME Telemetry Pipeline Alerts",
            topic_name="acme-telemetry-alerts"
        )
        
        if alert_email:
            self.alert_topic.add_subscription(
                subscriptions.EmailSubscription(alert_email)
            )
        
        # Create CloudWatch Dashboard
        self.dashboard = self.create_dashboard(generator_function, producer_function)
        
        # Create Alarms
        self.create_lambda_alarms(generator_function, "Generator")
        self.create_lambda_alarms(producer_function, "Producer")
        self.create_firehose_alarms()
        
        # Outputs
        CfnOutput(
            self, "DashboardURL",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.dashboard.dashboard_name}",
            description="URL to CloudWatch Dashboard"
        )
        
        CfnOutput(
            self, "AlertTopicArn",
            value=self.alert_topic.topic_arn,
            description="SNS Topic ARN for alerts"
        )
    
    def create_dashboard(self, generator_function: lambda_.IFunction, 
                        producer_function: lambda_.IFunction) -> cloudwatch.Dashboard:
        """Create CloudWatch dashboard"""
        
        dashboard = cloudwatch.Dashboard(
            self, "TelemetryDashboard",
            dashboard_name="ACME-Telemetry-Pipeline",
            period_override=cloudwatch.PeriodOverride.AUTO
        )
        
        # Lambda Metrics Row
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Generator Lambda Invocations",
                left=[
                    generator_function.metric_invocations(
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                ],
                right=[
                    generator_function.metric_errors(
                        statistic="Sum",
                        period=Duration.minutes(5),
                        color=cloudwatch.Color.RED
                    )
                ],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Producer Lambda Invocations",
                left=[
                    producer_function.metric_invocations(
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                ],
                right=[
                    producer_function.metric_errors(
                        statistic="Sum",
                        period=Duration.minutes(5),
                        color=cloudwatch.Color.RED
                    )
                ],
                width=12
            )
        )
        
        # Lambda Duration Row
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Duration",
                left=[
                    generator_function.metric_duration(
                        statistic="Average",
                        period=Duration.minutes(5)
                    ),
                    producer_function.metric_duration(
                        statistic="Average",
                        period=Duration.minutes(5)
                    )
                ],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Lambda Concurrent Executions",
                left=[
                    generator_function.metric("ConcurrentExecutions",
                        statistic="Maximum",
                        period=Duration.minutes(5)
                    ),
                    producer_function.metric("ConcurrentExecutions",
                        statistic="Maximum",
                        period=Duration.minutes(5)
                    )
                ],
                width=12
            )
        )
        
        # Firehose Metrics Row
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Firehose Incoming Records",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/KinesisFirehose",
                        metric_name="IncomingRecords",
                        dimensions_map={
                            "DeliveryStreamName": "AcmeTelemetry-MSK-to-S3"
                        },
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                ],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Firehose Data Freshness",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/KinesisFirehose",
                        metric_name="DataFreshness",
                        dimensions_map={
                            "DeliveryStreamName": "AcmeTelemetry-MSK-to-S3"
                        },
                        statistic="Maximum",
                        period=Duration.minutes(5)
                    )
                ],
                width=12
            )
        )
        
        # Custom Metrics Row
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Events Generated",
                left=[
                    cloudwatch.Metric(
                        namespace="AcmeTelemetry",
                        metric_name="EventsGenerated",
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                ],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Events Sent to MSK",
                left=[
                    cloudwatch.Metric(
                        namespace="AcmeTelemetry",
                        metric_name="EventsSent",
                        statistic="Sum",
                        period=Duration.minutes(5)
                    )
                ],
                right=[
                    cloudwatch.Metric(
                        namespace="AcmeTelemetry",
                        metric_name="EventErrors",
                        statistic="Sum",
                        period=Duration.minutes(5),
                        color=cloudwatch.Color.RED
                    )
                ],
                width=12
            )
        )
        
        # Add text widget with pipeline status
        dashboard.add_widgets(
            cloudwatch.TextWidget(
                markdown="""
# ACME Telemetry Pipeline Status

## Components
- **Generator Lambda**: Runs every 5 minutes via EventBridge
- **Producer Lambda**: Sends events to MSK
- **MSK Cluster**: Kafka message broker
- **Firehose**: Delivers data from MSK to S3
- **S3**: Data lake storage

## Expected Metrics
- **Event Generation**: 2,000-25,000 events per run
- **Frequency**: Every 5 minutes
- **Data Latency**: < 5 minutes to S3
- **Error Rate**: < 1%
                """,
                width=24,
                height=6
            )
        )
        
        return dashboard
    
    def create_lambda_alarms(self, function: lambda_.IFunction, name: str):
        """Create alarms for Lambda function"""
        
        # Error rate alarm
        error_alarm = cloudwatch.Alarm(
            self, f"{name}ErrorAlarm",
            alarm_name=f"ACME-Telemetry-{name}-Errors",
            alarm_description=f"Alert when {name} Lambda has errors",
            metric=function.metric_errors(
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=5,
            evaluation_periods=2,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )
        
        # Duration alarm
        duration_alarm = cloudwatch.Alarm(
            self, f"{name}DurationAlarm",
            alarm_name=f"ACME-Telemetry-{name}-Duration",
            alarm_description=f"Alert when {name} Lambda duration is high",
            metric=function.metric_duration(
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=30000 if name == "Generator" else 10000,  # 30s for generator, 10s for producer
            evaluation_periods=3,
            datapoints_to_alarm=2,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        duration_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )
        
        # Throttles alarm
        throttle_alarm = cloudwatch.Alarm(
            self, f"{name}ThrottleAlarm",
            alarm_name=f"ACME-Telemetry-{name}-Throttles",
            alarm_description=f"Alert when {name} Lambda is throttled",
            metric=function.metric_throttles(
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=2,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        throttle_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )
    
    def create_firehose_alarms(self):
        """Create alarms for Kinesis Firehose"""
        
        # Data freshness alarm
        freshness_alarm = cloudwatch.Alarm(
            self, "FirehoseFreshnessAlarm",
            alarm_name="ACME-Telemetry-Firehose-DataFreshness",
            alarm_description="Alert when Firehose data is stale",
            metric=cloudwatch.Metric(
                namespace="AWS/KinesisFirehose",
                metric_name="DataFreshness",
                dimensions_map={
                    "DeliveryStreamName": "AcmeTelemetry-MSK-to-S3"
                },
                statistic="Maximum",
                period=Duration.minutes(5)
            ),
            threshold=600,  # 10 minutes
            evaluation_periods=2,
            datapoints_to_alarm=2,
            treat_missing_data=cloudwatch.TreatMissingData.BREACHING
        )
        freshness_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )
        
        # Delivery success alarm
        delivery_alarm = cloudwatch.Alarm(
            self, "FirehoseDeliveryAlarm",
            alarm_name="ACME-Telemetry-Firehose-DeliverySuccess",
            alarm_description="Alert when Firehose delivery fails",
            metric=cloudwatch.Metric(
                namespace="AWS/KinesisFirehose",
                metric_name="DeliveryToS3.Success",
                dimensions_map={
                    "DeliveryStreamName": "AcmeTelemetry-MSK-to-S3"
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=0.95,  # 95% success rate
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            evaluation_periods=3,
            datapoints_to_alarm=2,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        delivery_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alert_topic)
        )