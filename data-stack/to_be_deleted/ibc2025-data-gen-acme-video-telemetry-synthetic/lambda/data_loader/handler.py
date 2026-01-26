import json
import boto3
import logging
import random
from typing import Dict, List, Any
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
athena_client = boto3.client('athena', region_name='eu-central-1')
s3_client = boto3.client('s3', region_name='eu-central-1')

# Configuration
DATABASE_NAME = 'acme_streaming_data'
OUTPUT_LOCATION = 's3://acme-telemetry-241533163649-eu-central-1/athena-results/'
CACHE_BUCKET = 'acme-telemetry-241533163649-eu-central-1'
CACHE_KEY = 'cache/reference-data.json'

def execute_athena_query(query: str) -> str:
    """Execute Athena query and return query execution ID"""
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': DATABASE_NAME},
        ResultConfiguration={'OutputLocation': OUTPUT_LOCATION}
    )
    return response['QueryExecutionId']

def wait_for_query_completion(query_id: str, max_wait: int = 30) -> bool:
    """Wait for Athena query to complete"""
    for _ in range(max_wait):
        response = athena_client.get_query_execution(QueryExecutionId=query_id)
        status = response['QueryExecution']['Status']['State']
        
        if status == 'SUCCEEDED':
            return True
        elif status in ['FAILED', 'CANCELLED']:
            logger.error(f"Query {query_id} failed with status: {status}")
            return False
        
        time.sleep(1)
    
    logger.error(f"Query {query_id} timed out after {max_wait} seconds")
    return False

def get_query_results(query_id: str) -> List[Dict]:
    """Get results from completed Athena query"""
    results = []
    paginator = athena_client.get_paginator('get_query_results')
    
    for page in paginator.paginate(QueryExecutionId=query_id):
        for row in page['ResultSet']['Rows'][1:]:  # Skip header row
            data = [col.get('VarCharValue', '') for col in row['Data']]
            results.append(data)
    
    return results

def load_titles() -> List[Dict[str, Any]]:
    """Load title data from Athena"""
    query = """
    SELECT 
        title_id,
        title_name,
        title_type,
        genre,
        duration_minutes,
        popularity_score,
        CASE 
            WHEN title_type = 'movie' THEN 'movie'
            WHEN title_type = 'series' THEN 'series'
            ELSE 'other'
        END as content_category
    FROM titles
    WHERE title_id IS NOT NULL
    ORDER BY popularity_score DESC NULLS LAST
    LIMIT 1000
    """
    
    query_id = execute_athena_query(query)
    
    if not wait_for_query_completion(query_id):
        raise Exception("Failed to load titles from Athena")
    
    results = get_query_results(query_id)
    titles = []
    
    for row in results:
        try:
            titles.append({
                'title_id': row[0],
                'title_name': row[1],
                'title_type': row[2],
                'genre': row[3],
                'duration_minutes': int(row[4]) if row[4] else 90,  # Default 90 mins
                'popularity_score': float(row[5]) if row[5] else 5.0,
                'content_category': row[6]
            })
        except (IndexError, ValueError) as e:
            logger.warning(f"Skipping malformed title row: {e}")
            continue
    
    logger.info(f"Loaded {len(titles)} titles from database")
    return titles

def load_customers(sample_size: int = 10000) -> List[Dict[str, Any]]:
    """Load customer data from Athena"""
    query = f"""
    SELECT 
        customer_id,
        subscription_tier,
        country,
        age_group,
        CASE 
            WHEN subscription_tier = 'premium' THEN 'active'
            WHEN subscription_tier = 'standard' THEN 'regular'
            ELSE 'new'
        END as customer_segment
    FROM customers
    WHERE customer_id IS NOT NULL
    ORDER BY RANDOM()
    LIMIT {sample_size}
    """
    
    query_id = execute_athena_query(query)
    
    if not wait_for_query_completion(query_id):
        raise Exception("Failed to load customers from Athena")
    
    results = get_query_results(query_id)
    customers = []
    
    for row in results:
        try:
            customers.append({
                'customer_id': row[0],
                'subscription_tier': row[1] if len(row) > 1 else 'standard',
                'country': row[2] if len(row) > 2 else 'United States',
                'age_group': row[3] if len(row) > 3 else 'adult',
                'customer_segment': row[4] if len(row) > 4 else 'regular'
            })
        except IndexError as e:
            logger.warning(f"Skipping malformed customer row: {e}")
            continue
    
    logger.info(f"Loaded {len(customers)} customers from database")
    return customers

def create_weighted_lists(titles: List[Dict], customers: List[Dict]) -> Dict:
    """Create weighted lists for realistic selection"""
    
    # Weight titles by popularity
    popular_titles = [t for t in titles if t.get('popularity_score', 0) > 7]
    regular_titles = [t for t in titles if 4 <= t.get('popularity_score', 0) <= 7]
    niche_titles = [t for t in titles if t.get('popularity_score', 0) < 4]
    
    # If no popularity scores, distribute evenly
    if not popular_titles and not regular_titles and not niche_titles:
        third = len(titles) // 3
        popular_titles = titles[:third]
        regular_titles = titles[third:2*third]
        niche_titles = titles[2*third:]
    
    # Weight customers by segment
    active_customers = [c for c in customers if c.get('customer_segment') == 'veteran']
    regular_customers = [c for c in customers if c.get('customer_segment') == 'regular']
    new_customers = [c for c in customers if c.get('customer_segment') == 'new']
    
    # If no segments, distribute evenly
    if not active_customers and not regular_customers and not new_customers:
        third = len(customers) // 3
        active_customers = customers[:third]
        regular_customers = customers[third:2*third]
        new_customers = customers[2*third:]
    
    return {
        'titles': {
            'popular': popular_titles[:200] if popular_titles else titles[:200],
            'regular': regular_titles[:300] if regular_titles else titles[200:500],
            'niche': niche_titles[:500] if niche_titles else titles[500:],
            'all': titles
        },
        'customers': {
            'active': active_customers[:3000] if active_customers else customers[:3000],
            'regular': regular_customers[:5000] if regular_customers else customers[3000:8000],
            'new': new_customers[:2000] if new_customers else customers[8000:],
            'all': customers
        },
        'metadata': {
            'total_titles': len(titles),
            'total_customers': len(customers),
            'timestamp': time.time()
        }
    }

def save_to_cache(data: Dict) -> None:
    """Save reference data to S3 cache"""
    try:
        s3_client.put_object(
            Bucket=CACHE_BUCKET,
            Key=CACHE_KEY,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        logger.info(f"Saved reference data to s3://{CACHE_BUCKET}/{CACHE_KEY}")
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")
        raise

def load_from_cache() -> Dict:
    """Load reference data from S3 cache"""
    try:
        response = s3_client.get_object(Bucket=CACHE_BUCKET, Key=CACHE_KEY)
        data = json.loads(response['Body'].read())
        
        # Check if cache is fresh (less than 24 hours old)
        if time.time() - data['metadata']['timestamp'] < 86400:
            logger.info("Using cached reference data")
            return data
        else:
            logger.info("Cache is stale, will refresh")
            return None
    except Exception as e:
        logger.info(f"No cache found or error loading: {e}")
        return None

def lambda_handler(event, context):
    """
    Load reference data for telemetry generation
    Can be called directly or return cached data
    """
    try:
        # Check if force refresh is requested
        force_refresh = event.get('force_refresh', False)
        
        # Try to load from cache first
        if not force_refresh:
            cached_data = load_from_cache()
            if cached_data:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'source': 'cache',
                        'data': cached_data
                    })
                }
        
        # Load fresh data from Athena
        logger.info("Loading fresh reference data from Athena")
        
        titles = load_titles()
        customers = load_customers()
        
        if not titles or not customers:
            raise Exception("Failed to load required reference data")
        
        # Create weighted lists
        reference_data = create_weighted_lists(titles, customers)
        
        # Save to cache
        save_to_cache(reference_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'source': 'fresh',
                'data': reference_data
            })
        }
        
    except Exception as e:
        logger.error(f"Error in data loader: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }