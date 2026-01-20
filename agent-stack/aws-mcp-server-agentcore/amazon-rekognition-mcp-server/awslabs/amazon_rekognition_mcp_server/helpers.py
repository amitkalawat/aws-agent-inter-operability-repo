# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper functions for the Amazon Rekognition MCP Server."""

import boto3
import functools
import os
import re
import urllib.request
from awslabs.amazon_rekognition_mcp_server import __version__
from botocore.config import Config
from loguru import logger
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, Union, cast


T = TypeVar('T', bound=Callable[..., Awaitable[Any]])


def get_base_dir() -> Optional[str]:
    """Get the base directory from environment variables.

    Returns:
        The base directory path if set, None otherwise.
    """
    return os.environ.get('BASE_DIR')


def get_aws_session():
    """Create an AWS session using credentials from environment variables."""
    profile_name = os.environ.get('AWS_PROFILE')
    region = os.environ.get('AWS_REGION', 'us-east-1')

    if profile_name:
        logger.debug(f'Using AWS profile: {profile_name}')
        return boto3.Session(profile_name=profile_name, region_name=region)
    else:
        logger.debug('Using default AWS credential chain')
        return boto3.Session(region_name=region)


def get_rekognition_client():
    """Get a Rekognition client."""
    session = get_aws_session()
    config = Config(user_agent_extra=f'awslabs/mcp/amazon_rekognition_mcp_server/{__version__}')
    return session.client('rekognition', config=config)


def handle_exceptions(func: T) -> T:
    """Decorator to handle exceptions in a consistent way."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f'Error in {func.__name__}: {e}')
            raise ValueError(f'Error in {func.__name__}: {str(e)}')

    return cast(T, wrapper)


def sanitize_path(file_path: str, base_dir: Optional[str] = None) -> Path:
    """Sanitize and validate a file path to prevent path traversal attacks.

    Args:
        file_path: The input file path to sanitize
        base_dir: Optional base directory to restrict paths to

    Returns:
        Path: A sanitized Path object

    Raises:
        ValueError: If the path is invalid or attempts to traverse outside base_dir
    """
    # Convert to absolute path if base_dir is provided
    if base_dir:
        base_path = Path(base_dir).resolve()
        try:
            # Resolve the path relative to base_dir
            full_path = (base_path / file_path).resolve()
            # Check if the resolved path is still within base_dir
            if not str(full_path).startswith(str(base_path)):
                raise ValueError(f'Path {file_path} attempts to traverse outside base directory')
            return full_path
        except Exception as e:
            raise ValueError(f'Invalid path: {str(e)}')

    # If no base_dir, just sanitize the path
    try:
        return Path(file_path).resolve()
    except Exception as e:
        raise ValueError(f'Invalid path: {str(e)}')


def get_image_bytes(image_source: str) -> Dict[str, Any]:
    """Get image data from a local file, S3 URI, or HTTP(S) URL.

    Supports three input formats:
    1. Local file path: /path/to/image.jpg
    2. S3 URI: s3://bucket-name/key/path/image.jpg
    3. HTTP(S) URL: https://bucket.s3.region.amazonaws.com/key?signature... (presigned URLs)

    Args:
        image_source: Path to the image file, S3 URI, or HTTP(S) URL.

    Returns:
        Dict with either:
        - 'Bytes' key containing the image bytes (for local files and HTTP URLs)
        - 'S3Object' key containing bucket and key (for S3 URIs)

    Raises:
        ValueError: If the image cannot be read from the source.
    """
    # Check if it's an S3 URI (s3://bucket/key)
    if image_source.startswith('s3://'):
        match = re.match(r's3://([^/]+)/(.+)', image_source)
        if not match:
            raise ValueError(f'Invalid S3 URI format: {image_source}')
        bucket = match.group(1)
        key = match.group(2)
        logger.debug(f'Using S3Object format: bucket={bucket}, key={key}')
        return {'S3Object': {'Bucket': bucket, 'Name': key}}

    # Check if it's an HTTP(S) URL (including presigned S3 URLs)
    if image_source.startswith('http://') or image_source.startswith('https://'):
        logger.debug(f'Downloading image from URL: {image_source[:100]}...')
        try:
            # Create a request with a user agent to avoid blocks
            req = urllib.request.Request(
                image_source,
                headers={'User-Agent': 'Amazon-Rekognition-MCP-Server/1.0'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                image_bytes = response.read()
                logger.debug(f'Downloaded {len(image_bytes)} bytes from URL')
                return {'Bytes': image_bytes}
        except Exception as e:
            logger.error(f'Error downloading image from URL: {e}')
            raise ValueError(f'Error downloading image from URL: {str(e)}')

    # Otherwise treat as local file path
    path = sanitize_path(image_source, get_base_dir())
    if not path.exists():
        raise ValueError(f'Image file not found: {image_source}')

    try:
        with open(path, 'rb') as image_file:
            return {'Bytes': image_file.read()}
    except Exception as e:
        raise ValueError(f'Error reading image file: {str(e)}')
