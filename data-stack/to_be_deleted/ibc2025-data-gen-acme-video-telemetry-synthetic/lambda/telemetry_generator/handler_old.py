import json
import random
import uuid
import boto3
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda client for invoking MSK producer
lambda_client = boto3.client('lambda')

# MSK Producer function name from environment variable
MSK_PRODUCER_FUNCTION = os.environ.get('MSK_PRODUCER_FUNCTION_NAME', 'AcmeTelemetry-Producer')

def generate_telemetry_events(viewer_count: int) -> list:
    """Generate realistic telemetry events for video streaming"""
    events = []
    
    # Content library
    titles = [f"TITLE_{uuid.uuid4().hex[:8]}" for _ in range(50)]
    
    # Event types with weights
    event_types = ['start', 'stop', 'pause', 'resume', 'complete']
    event_weights = [0.15, 0.35, 0.15, 0.15, 0.20]
    
    # Device types with weights
    device_types = ['mobile', 'web', 'tv', 'tablet']
    device_weights = [0.35, 0.25, 0.30, 0.10]
    
    # Quality levels
    quality_levels = ['SD', 'HD', '4K']
    quality_weights = [0.25, 0.60, 0.15]
    
    # ISPs and connection types
    isps = ['Comcast', 'AT&T', 'Verizon', 'Spectrum', 'Cox', 'Frontier', 'CenturyLink']
    connection_types = ['wifi', 'mobile', 'fiber', 'cable', 'dsl', 'satellite']
    
    # Geographic data
    countries = ['United States', 'Canada', 'United Kingdom']
    us_states = ['California', 'Texas', 'Florida', 'New York', 'Illinois', 'Washington', 'Oregon', 'Nevada']
    cities = ['Los Angeles', 'New York', 'Chicago', 'Houston', 'Seattle', 'Portland', 'Las Vegas']
    
    for _ in range(viewer_count):
        # Generate consistent user data
        customer_id = f"CUST_{uuid.uuid4().hex[:8]}"
        
        # Generate event
        event_type = random.choices(event_types, weights=event_weights)[0]
        device_type = random.choices(device_types, weights=device_weights)[0]
        quality = random.choices(quality_levels, weights=quality_weights)[0]
        
        # Device-specific OS
        if device_type == 'mobile':
            device_os = random.choice(['iOS', 'Android'])
        elif device_type == 'web':
            device_os = random.choice(['Windows', 'macOS', 'Linux', 'ChromeOS'])
        elif device_type == 'tv':
            device_os = random.choice(['Roku OS', 'Fire TV', 'Apple TV', 'Android TV', 'Smart TV OS'])
        else:  # tablet
            device_os = random.choice(['iOS', 'Android'])
        
        # Quality-based bandwidth
        if quality == '4K':
            bandwidth = round(random.uniform(15, 30), 2)
        elif quality == 'HD':
            bandwidth = round(random.uniform(5, 15), 2)
        else:  # SD
            bandwidth = round(random.uniform(1.5, 5), 2)
        
        # Watch duration and position
        total_duration = random.randint(300, 7200)  # 5 min to 2 hours
        if event_type == 'start':
            watch_duration = 0
            position = random.randint(0, total_duration)
        elif event_type == 'complete':
            watch_duration = random.randint(int(total_duration * 0.8), total_duration)
            position = random.randint(0, total_duration)
        else:
            watch_duration = random.randint(0, total_duration)
            position = random.randint(0, total_duration)
        
        # Buffering simulation (more likely with lower bandwidth)
        if bandwidth < 3:
            buffering_events = random.randint(0, 5)
            buffering_duration = random.randint(0, 30) if buffering_events > 0 else 0
            error_count = random.randint(0, 2)
        else:
            buffering_events = 0 if random.random() > 0.1 else random.randint(1, 2)
            buffering_duration = random.randint(0, 10) if buffering_events > 0 else 0
            error_count = 0 if random.random() > 0.05 else 1
        
        # Geographic data
        country = random.choice(countries)
        state = random.choice(us_states) if country == 'United States' else random.choice(['', 'Ontario', 'Quebec', 'British Columbia'])
        
        event = {
            'event_id': f"EVENT_{uuid.uuid4().hex[:8]}",
            'customer_id': customer_id,
            'title_id': random.choice(titles),
            'session_id': f"SESSION_{uuid.uuid4().hex[:8]}",
            'event_type': event_type,
            'event_timestamp': datetime.utcnow().isoformat() + 'Z',
            'watch_duration_seconds': watch_duration,
            'position_seconds': position,
            'completion_percentage': round((position / total_duration) * 100, 2) if total_duration > 0 else 0,
            'device_type': device_type,
            'device_id': f"DEVICE_{uuid.uuid4().hex[:8]}",
            'device_os': device_os,
            'app_version': f"5.{random.randint(0, 2)}.{random.randint(0, 9)}",
            'quality': quality,
            'bandwidth_mbps': bandwidth,
            'buffering_events': buffering_events,
            'buffering_duration_seconds': buffering_duration,
            'error_count': error_count,
            'ip_address': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            'country': country,
            'state': state,
            'city': random.choice(cities),
            'isp': random.choice(isps),
            'connection_type': random.choice(connection_types)
        }
        
        events.append(event)
    
    return events

def get_viewer_count():
    """Determine viewer count based on time of day"""
    current_hour = datetime.utcnow().hour
    
    # Simulate viewing patterns
    if 2 <= current_hour < 6:  # Late night/early morning (lowest)
        return random.randint(2000, 5000), 'late_night'
    elif 6 <= current_hour < 10:  # Morning
        return random.randint(5000, 10000), 'morning'
    elif 10 <= current_hour < 14:  # Midday
        return random.randint(8000, 15000), 'midday'
    elif 14 <= current_hour < 18:  # Afternoon
        return random.randint(10000, 18000), 'afternoon'
    elif 18 <= current_hour < 22:  # Prime time (highest)
        return random.randint(15000, 25000), 'prime_time'
    else:  # Evening
        return random.randint(8000, 15000), 'evening'

def send_to_msk_producer(events, batch_id):
    """Send events to MSK producer Lambda in batches"""
    # Split events into batches of 100 to avoid Lambda payload limits
    batch_size = 100
    success_count = 0
    error_count = 0
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        
        try:
            # Invoke MSK producer Lambda
            response = lambda_client.invoke(
                FunctionName=MSK_PRODUCER_FUNCTION,
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'events': batch,
                    'batch_id': batch_id,
                    'batch_number': i // batch_size
                })
            )
            
            # Check response
            result = json.loads(response['Payload'].read())
            if response['StatusCode'] == 200:
                success_count += len(batch)
                logger.info(f"Successfully sent batch {i//batch_size} with {len(batch)} events")
            else:
                error_count += len(batch)
                logger.error(f"Error in batch {i//batch_size}: {result}")
                
        except Exception as e:
            error_count += len(batch)
            logger.error(f"Error sending events to MSK producer: {str(e)}")
    
    return success_count, error_count

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Check if this is a test invocation with specific parameters
        if event.get('test'):
            viewer_count = event.get('batch_size', random.randint(100, 500))
            time_period = 'test'
        else:
            # Get viewer count based on time of day
            viewer_count, time_period = get_viewer_count()
        
        logger.info(f"Generating events for {viewer_count} viewers in {time_period} period")
        
        # Load reference data
        reference_data = load_reference_data()
        
        if not reference_data:
            logger.warning("Could not load reference data, using random generation")
        
        # Generate telemetry events
        events = generate_telemetry_events(viewer_count, reference_data)
        
        # Create batch ID for tracking
        batch_id = str(uuid.uuid4())
        
        # Send to MSK producer
        success_count, error_count = send_to_msk_producer(events, batch_id)
        
        # Return response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Telemetry events generated successfully',
                'batch_id': batch_id,
                'viewer_count': viewer_count,
                'time_period': time_period,
                'success_count': success_count,
                'error_count': error_count
            })
        }
        
        logger.info(f"Generation complete: {success_count} successful, {error_count} errors")
        return response
        
    except Exception as e:
        logger.error(f"Error in telemetry generator: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }