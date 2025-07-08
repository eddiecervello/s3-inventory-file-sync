import os
import logging
import concurrent.futures
import time
import re
from pathlib import Path, PurePath
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Tuple, Optional
from .config import SyncConfig

def _sanitize_sku(sku: str) -> str:
    """Sanitize SKU to prevent path traversal and injection attacks.
    
    Args:
        sku: Raw SKU string
        
    Returns:
        Sanitized SKU string safe for file operations
        
    Raises:
        ValueError: If SKU contains invalid characters
    """
    if not sku or not sku.strip():
        raise ValueError("SKU cannot be empty")
    
    # Remove any path traversal attempts
    sanitized = sku.strip()
    if '..' in sanitized or '/' in sanitized or '\\' in sanitized:
        raise ValueError(f"SKU contains invalid path characters: {sku}")
    
    # Only allow alphanumeric, hyphens, underscores, and periods
    if not re.match(r'^[a-zA-Z0-9._-]+$', sanitized):
        raise ValueError(f"SKU contains invalid characters: {sku}")
    
    # Limit length to prevent abuse
    if len(sanitized) > 100:
        raise ValueError(f"SKU too long (max 100 chars): {sku}")
    
    return sanitized


def _validate_file_path(base_path: str, file_path: str) -> str:
    """Validate that file path is within the allowed base directory.
    
    Args:
        base_path: Base directory path
        file_path: File path to validate
        
    Returns:
        Validated absolute file path
        
    Raises:
        ValueError: If path is outside base directory
    """
    base_abs = Path(base_path).resolve()
    file_abs = Path(file_path).resolve()
    
    try:
        file_abs.relative_to(base_abs)
    except ValueError:
        raise ValueError(f"File path outside allowed directory: {file_path}")
    
    return str(file_abs)


def download_sku_file(s3_client, config: SyncConfig, sku: str, file_extensions: List[str] = ['.pdf'], max_retries: int = 3) -> Tuple[str, bool, Optional[str]]:
    """Download file for a single SKU with security validation and retry logic.
    
    Args:
        s3_client: Boto3 S3 client
        config: Sync configuration
        sku: SKU identifier
        file_extensions: List of file extensions to try (default: ['.pdf'])
        max_retries: Maximum number of retry attempts
    
    Returns:
        Tuple of (sku, success, downloaded_file_path)
    """
    try:
        # Sanitize SKU to prevent security issues
        safe_sku = _sanitize_sku(sku)
    except ValueError as e:
        logging.error(f"Invalid SKU '{sku}': {e}")
        return sku, False, None
    
    for ext in file_extensions:
        # Validate file extension
        if not re.match(r'^\.[a-zA-Z0-9]+$', ext):
            logging.warning(f"Skipping invalid file extension: {ext}")
            continue
            
        file_key = f"{config.s3_prefix}{safe_sku}{ext}"
        local_filename = f"{safe_sku}{ext}"
        
        try:
            # Validate the local file path is safe
            local_file_path = _validate_file_path(
                config.local_download_path, 
                os.path.join(config.local_download_path, local_filename)
            )
        except ValueError as e:
            logging.error(f"Invalid file path for SKU '{sku}': {e}")
            continue
        
        # Skip if file already exists
        if os.path.exists(local_file_path):
            logging.debug(f"File already exists: {local_file_path}")
            return sku, True, local_file_path
        
        # Retry logic for download
        for attempt in range(max_retries):
            try:
                s3_client.download_file(config.bucket_name, file_key, local_file_path)
                logging.info(f"Downloaded {file_key} to {local_file_path}")
                return sku, True, local_file_path
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == 'NoSuchKey':
                    logging.debug(f"File not found: {file_key}")
                    break  # No point retrying for missing files
                elif error_code in ['AccessDenied', 'Forbidden']:
                    logging.error(f"Access denied for {file_key}")
                    break  # No point retrying for permission errors
                else:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logging.warning(f"Download failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        logging.error(f"Failed to download {file_key} after {max_retries} attempts: {e}")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logging.warning(f"Unexpected error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to download {file_key} after {max_retries} attempts: {e}")
    
    return sku, False, None

def sync_skus(config: SyncConfig, sku_list: List[str], file_extensions: List[str] = ['.pdf']) -> List[Tuple[str, bool]]:
    """Sync multiple SKUs from S3 with security validation and error handling.
    
    Args:
        config: Sync configuration
        sku_list: List of SKUs to sync
        file_extensions: List of file extensions to try (default: ['.pdf'])
    
    Returns:
        List of (sku, success) tuples
        
    Raises:
        ValueError: If configuration is invalid
        NoCredentialsError: If AWS credentials are not available
    """
    # Validate configuration
    if not config.bucket_name or not config.bucket_name.strip():
        raise ValueError("Bucket name cannot be empty")
    
    if not config.local_download_path or not config.local_download_path.strip():
        raise ValueError("Local download path cannot be empty")
    
    # Validate bucket name format (basic S3 bucket name validation)
    if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', config.bucket_name.lower()):
        raise ValueError(f"Invalid bucket name format: {config.bucket_name}")
    
    # Validate file extensions
    for ext in file_extensions:
        if not re.match(r'^\.[a-zA-Z0-9]+$', ext):
            raise ValueError(f"Invalid file extension format: {ext}")
    
    # Validate and create download directory
    try:
        download_path = Path(config.local_download_path).resolve()
        download_path.mkdir(parents=True, exist_ok=True)
        
        # Ensure we can write to the directory
        if not os.access(download_path, os.W_OK):
            raise ValueError(f"Cannot write to download directory: {download_path}")
            
    except Exception as e:
        raise ValueError(f"Invalid download path: {e}")
    
    # Validate SKU list
    if not sku_list:
        logging.warning("No SKUs provided")
        return []
    
    # Limit the number of SKUs to prevent abuse
    if len(sku_list) > 10000:
        raise ValueError(f"Too many SKUs (max 10000): {len(sku_list)}")
    
    try:
        # Initialize S3 client with error handling
        s3_client = boto3.client('s3')
        
        # Test S3 connection and permissions
        try:
            s3_client.head_bucket(Bucket=config.bucket_name)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucket':
                raise ValueError(f"S3 bucket does not exist: {config.bucket_name}")
            elif error_code in ['AccessDenied', 'Forbidden']:
                raise ValueError(f"Access denied to S3 bucket: {config.bucket_name}")
            else:
                raise ValueError(f"Cannot access S3 bucket: {e}")
        except NoCredentialsError:
            raise NoCredentialsError("AWS credentials not found. Please configure AWS credentials.")
            
    except Exception as e:
        logging.error(f"Failed to initialize S3 client: {e}")
        raise
    
    results = []
    completed = 0
    total = len(sku_list)
    
    # Limit concurrent workers to prevent resource exhaustion
    max_workers = min(config.max_workers, 20, len(sku_list))
    
    logging.info(f"Starting sync of {total} SKUs with {max_workers} workers")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_sku = {}
        for sku in sku_list:
            try:
                future = executor.submit(download_sku_file, s3_client, config, sku, file_extensions)
                future_to_sku[future] = sku
            except Exception as e:
                logging.error(f"Failed to submit task for SKU {sku}: {e}")
                results.append((sku, False))
                completed += 1
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_sku):
            sku = future_to_sku[future]
            try:
                sku_result, success, file_path = future.result(timeout=30)  # Add timeout
                results.append((sku_result, success))
                completed += 1
                
                # Progress logging every 10 items or at completion
                if completed % 10 == 0 or completed == total:
                    logging.info(f"Progress: {completed}/{total} SKUs processed")
                    
            except concurrent.futures.TimeoutError:
                logging.error(f"Timeout processing SKU {sku}")
                results.append((sku, False))
                completed += 1
            except Exception as e:
                logging.error(f"Error processing SKU {sku}: {e}")
                results.append((sku, False))
                completed += 1
    
    logging.info(f"Sync completed: {completed}/{total} SKUs processed")
    return results
