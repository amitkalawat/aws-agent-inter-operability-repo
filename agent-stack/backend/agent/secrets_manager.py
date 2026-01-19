#!/usr/bin/env python3
"""
AWS Secrets Manager Client for ACME Corp Chatbot
Handles secure retrieval and caching of MCP credentials
"""

import boto3
import json
import time
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


class SecretsManager:
    """AWS Secrets Manager client with caching"""
    
    def __init__(self, region_name: str = "eu-central-1"):
        self.region_name = region_name
        self.client = boto3.client('secretsmanager', region_name=region_name)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = 3600  # 1 hour cache TTL
        
    def get_secret(self, secret_name: str, cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager with caching
        
        Args:
            secret_name: Name of the secret in Secrets Manager
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            
        Returns:
            Dictionary containing secret key-value pairs
            
        Raises:
            Exception: If secret cannot be retrieved
        """
        ttl = cache_ttl or self._default_ttl
        current_time = time.time()
        
        # Check cache first
        if secret_name in self._cache:
            cached_data = self._cache[secret_name]
            if current_time < cached_data['expires_at']:
                print(f"✅ Retrieved {secret_name} from cache")
                return cached_data['data']
        
        # Retrieve from Secrets Manager
        try:
            print(f"🔑 Retrieving {secret_name} from AWS Secrets Manager...")
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse the secret value
            secret_string = response['SecretString']
            secret_data = json.loads(secret_string)
            
            # Cache the result
            self._cache[secret_name] = {
                'data': secret_data,
                'expires_at': current_time + ttl,
                'retrieved_at': current_time
            }
            
            print(f"✅ Successfully retrieved and cached {secret_name}")
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'DecryptionFailureException':
                raise Exception("Secrets Manager can't decrypt the protected secret text using the provided KMS key")
            elif error_code == 'InternalServiceErrorException':
                raise Exception("An error occurred on the server side")
            elif error_code == 'InvalidParameterException':
                raise Exception("You provided an invalid value for a parameter")
            elif error_code == 'InvalidRequestException':
                raise Exception("You provided a parameter value that is not valid for the current state of the resource")
            elif error_code == 'ResourceNotFoundException':
                raise Exception(f"The requested secret {secret_name} was not found")
            else:
                raise Exception(f"Failed to retrieve secret {secret_name}: {str(e)}")
        except json.JSONDecodeError:
            raise Exception(f"Secret {secret_name} does not contain valid JSON")
        except Exception as e:
            raise Exception(f"Unexpected error retrieving secret {secret_name}: {str(e)}")
    
    def get_mcp_credentials(self) -> Dict[str, str]:
        """
        Get MCP credentials from the standard ACME chatbot secret
        
        Returns:
            Dictionary containing MCP configuration
        """
        secret_name = "acme-chatbot/mcp-credentials"
        
        try:
            credentials = self.get_secret(secret_name)
            
            # Validate required fields
            required_fields = [
                'MCP_COGNITO_POOL_ID',
                'MCP_COGNITO_REGION', 
                'MCP_COGNITO_CLIENT_ID',
                'MCP_COGNITO_CLIENT_SECRET',
                'MCP_DOCS_URL'
            ]
            
            # Optional fields
            optional_fields = [
                'MCP_DATAPROC_URL'
            ]
            
            missing_fields = [field for field in required_fields if field not in credentials]
            if missing_fields:
                raise Exception(f"Missing required fields in secret: {missing_fields}")
            
            # Check for optional fields and log availability
            available_optional = [field for field in optional_fields if field in credentials and credentials[field]]
            if available_optional:
                print(f"✅ Optional MCP services available: {available_optional}")
            
            print(f"✅ MCP credentials validated successfully")
            return credentials
            
        except Exception as e:
            print(f"⚠️  Could not retrieve MCP credentials: {e}")
            print("ℹ️  AWS Documentation features will be disabled")
            raise
    
    def clear_cache(self, secret_name: Optional[str] = None):
        """
        Clear cached secrets
        
        Args:
            secret_name: Specific secret to clear (if None, clears all)
        """
        if secret_name:
            if secret_name in self._cache:
                del self._cache[secret_name]
                print(f"🗑️  Cleared cache for {secret_name}")
        else:
            self._cache.clear()
            print("🗑️  Cleared all cached secrets")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached secrets
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        cache_info = {}
        
        for secret_name, data in self._cache.items():
            cache_info[secret_name] = {
                'retrieved_at': time.ctime(data['retrieved_at']),
                'expires_at': time.ctime(data['expires_at']),
                'is_expired': current_time >= data['expires_at'],
                'ttl_remaining': max(0, data['expires_at'] - current_time)
            }
        
        return cache_info


# Global instance for use across the application
secrets_manager = SecretsManager()