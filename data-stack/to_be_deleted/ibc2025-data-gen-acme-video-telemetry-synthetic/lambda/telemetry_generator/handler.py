import json
import random
import uuid
import boto3
import os
from datetime import datetime, timedelta
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda client for invoking MSK producer and data loader
lambda_client = boto3.client('lambda')

# Function names from environment variables
MSK_PRODUCER_FUNCTION = os.environ.get('MSK_PRODUCER_FUNCTION_NAME', 'AcmeTelemetry-Producer')
DATA_LOADER_FUNCTION = os.environ.get('DATA_LOADER_FUNCTION_NAME', 'AcmeTelemetry-DataLoader')

# Cache for reference data
REFERENCE_DATA_CACHE = None
CACHE_TIMESTAMP = 0
CACHE_TTL = 3600  # 1 hour

def load_reference_data():
    """Load reference data from Data Loader Lambda"""
    global REFERENCE_DATA_CACHE, CACHE_TIMESTAMP
    
    # Check if cache is still valid
    if REFERENCE_DATA_CACHE and (time.time() - CACHE_TIMESTAMP) < CACHE_TTL:
        logger.info("Using cached reference data")
        return REFERENCE_DATA_CACHE
    
    try:
        logger.info("Loading reference data from Data Loader")
        response = lambda_client.invoke(
            FunctionName=DATA_LOADER_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps({'force_refresh': False})
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            if body.get('success'):
                REFERENCE_DATA_CACHE = body.get('data')
                CACHE_TIMESTAMP = time.time()
                logger.info(f"Loaded {REFERENCE_DATA_CACHE['metadata']['total_titles']} titles and {REFERENCE_DATA_CACHE['metadata']['total_customers']} customers")
                return REFERENCE_DATA_CACHE
    except Exception as e:
        logger.error(f"Failed to load reference data: {str(e)}")
    
    # Return None if loading failed
    return None

def select_title(reference_data, event_type):
    """Select a title based on popularity and event type"""
    if not reference_data or not reference_data.get('titles'):
        logger.warning("No reference_data or titles, using random")
        return f"TITLE_{uuid.uuid4().hex[:8]}"
    
    # For start events, bias towards popular content
    if event_type == 'start':
        # 70% popular, 25% regular, 5% niche
        pools = [
            reference_data['titles'].get('popular', []),
            reference_data['titles'].get('regular', []),
            reference_data['titles'].get('niche', [])
        ]
        # Filter out empty pools
        pools = [p for p in pools if p]
        if pools:
            weights = [0.7, 0.25, 0.05][:len(pools)]
            title_pool = random.choices(pools, weights=weights, k=1)[0]
        else:
            title_pool = reference_data['titles'].get('all', [])
    else:
        # For other events, more balanced distribution
        pools = [
            reference_data['titles'].get('popular', []),
            reference_data['titles'].get('regular', []),
            reference_data['titles'].get('niche', [])
        ]
        pools = [p for p in pools if p]
        if pools:
            weights = [0.5, 0.35, 0.15][:len(pools)]
            title_pool = random.choices(pools, weights=weights, k=1)[0]
        else:
            title_pool = reference_data['titles'].get('all', [])
    
    if title_pool:
        selected = random.choice(title_pool)
        if isinstance(selected, dict):
            title_id = selected.get('title_id')
            logger.debug(f"Selected title: {title_id} from {selected.get('title_name', 'unknown')}")
            return title_id
        else:
            logger.warning(f"Title pool item is not a dict: {type(selected)}")
            return selected
    else:
        logger.warning("Empty title pool, using random")
        return f"TITLE_{uuid.uuid4().hex[:8]}"

def generate_telemetry_events(viewer_count: int, reference_data=None) -> list:
    """Generate realistic telemetry events for video streaming"""
    events = []
    
    # Use reference data if available
    if reference_data:
        all_titles = reference_data['titles'].get('all', [])
        all_customers = reference_data['customers'].get('all', [])
        active_customers = reference_data['customers'].get('active', [])
        regular_customers = reference_data['customers'].get('regular', [])
        new_customers = reference_data['customers'].get('new', [])
    else:
        # Fallback to random generation
        all_titles = [f"TITLE_{uuid.uuid4().hex[:8]}" for _ in range(50)]
        all_customers = []
        active_customers = []
        regular_customers = []
        new_customers = []
    
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
        # Select customer from reference data or generate random
        if reference_data and all_customers:
            # Weighted customer selection: 60% regular, 30% active, 10% new
            pools = [regular_customers, active_customers, new_customers]
            pools = [p for p in pools if p]  # Filter out empty pools
            
            if pools:
                weights = [0.6, 0.3, 0.1][:len(pools)]
                customer_pool = random.choices(pools, weights=weights, k=1)[0]
                customer_data = random.choice(customer_pool)
                customer_id = customer_data.get('customer_id')
                customer_country = customer_data.get('country', 'United States')
            else:
                # Use all customers if no segments
                customer_data = random.choice(all_customers) if all_customers else None
                if customer_data:
                    customer_id = customer_data.get('customer_id')
                    customer_country = customer_data.get('country', 'United States')
                else:
                    customer_id = f"CUST_{uuid.uuid4().hex[:8]}"
                    customer_country = random.choice(countries)
        else:
            customer_id = f"CUST_{uuid.uuid4().hex[:8]}"
            customer_country = random.choice(countries)
        
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
            position = 0
        elif event_type == 'complete':
            watch_duration = random.randint(int(total_duration * 0.8), total_duration)
            position = total_duration
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
        
        # Geographic data - use customer's country if available
        country = customer_country
        state = random.choice(us_states) if country == 'United States' else random.choice(['', 'Ontario', 'Quebec', 'British Columbia'])
        
        # Select title with proper weighting
        title_id = select_title(reference_data, event_type)
        
        event = {
            'event_id': f"EVENT_{uuid.uuid4().hex[:8]}",
            'customer_id': customer_id,
            'title_id': title_id,
            'session_id': f"SESSION_{uuid.uuid4().hex[:8]}",
            'event_type': event_type,
            'event_timestamp': datetime.utcnow().isoformat() + 'Z',
            'watch_duration_seconds': watch_duration,
            'position_seconds': position,
            'completion_percentage': round((position / total_duration) * 100, 2) if total_duration > 0 else 0,
            'device_type': device_type,
            'device_id': f"DEVICE_{uuid.uuid4().hex[:8]}",
            'device_os': device_os,
            'app_version': f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
            'quality': quality,
            'bandwidth_mbps': bandwidth,
            'buffering_events': buffering_events,
            'buffering_duration_seconds': buffering_duration,
            'error_count': error_count,
            'ip_address': f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
            'country': country,
            'state': state,
            'city': random.choice(cities) if state else '',
            'isp': random.choice(isps),
            'connection_type': random.choice(connection_types)
        }
        
        events.append(event)
    
    return events

def get_viewer_count():
    """Determine viewer count based on time of day"""
    current_hour = datetime.utcnow().hour
    
    # Simulate different viewing patterns throughout the day
    if 0 <= current_hour < 6:
        # Late night/early morning - low viewership
        viewer_count = random.randint(1000, 3000)
        period = 'late_night'
    elif 6 <= current_hour < 12:
        # Morning - moderate viewership
        viewer_count = random.randint(3000, 6000)
        period = 'morning'
    elif 12 <= current_hour < 18:
        # Afternoon - moderate to high viewership
        viewer_count = random.randint(5000, 10000)
        period = 'afternoon'
    else:
        # Evening/prime time - peak viewership
        viewer_count = random.randint(8000, 25000)
        period = 'prime_time'
    
    return viewer_count, period

def send_to_msk_producer(events, batch_id):
    """Send events to MSK producer Lambda in batches"""
    batch_size = 100  # Send 100 events per invocation
    success_count = 0
    error_count = 0
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        
        try:
            # Invoke MSK producer Lambda
            response = lambda_client.invoke(
                FunctionName=MSK_PRODUCER_FUNCTION,
                InvocationType='Event',  # Asynchronous invocation
                Payload=json.dumps({
                    'events': batch,
                    'batch_id': batch_id,
                    'batch_number': i // batch_size
                })
            )
            
            if response['StatusCode'] in [202, 200]:
                success_count += len(batch)
                logger.info(f"Successfully sent batch {i // batch_size} with {len(batch)} events")
            else:
                error_count += len(batch)
                logger.error(f"Failed to send batch {i // batch_size}: StatusCode {response['StatusCode']}")
                
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
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Telemetry events generated successfully',
                'batch_id': batch_id,
                'viewer_count': viewer_count,
                'time_period': time_period,
                'success_count': success_count,
                'error_count': error_count,
                'using_real_data': reference_data is not None
            })
        }
        
    except Exception as e:
        logger.error(f"Error in telemetry generator: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }