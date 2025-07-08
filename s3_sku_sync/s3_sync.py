import os
import logging
import concurrent.futures
import time
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from typing import List, Tuple, Optional
from .config import SyncConfig

def download_sku_file(s3_client, config: SyncConfig, sku: str, file_extensions: List[str] = ['.pdf']) -> Tuple[str, bool, Optional[str]]:
    """Download file for a single SKU.
    
    Args:
        s3_client: Boto3 S3 client
        config: Sync configuration
        sku: SKU identifier
        file_extensions: List of file extensions to try (default: ['.pdf'])
    
    Returns:
        Tuple of (sku, success, downloaded_file_path)
    """
    for ext in file_extensions:
        file_key = f"{config.s3_prefix}{sku}{ext}"
        local_file_path = os.path.join(config.local_download_path, f"{sku}{ext}")
        
        # Skip if file already exists
        if os.path.exists(local_file_path):
            logging.debug(f"File already exists: {local_file_path}")
            return sku, True, local_file_path
        
        try:
            s3_client.download_file(config.bucket_name, file_key, local_file_path)
            logging.info(f"Downloaded {file_key} to {local_file_path}")
            return sku, True, local_file_path
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                logging.debug(f"File not found: {file_key}")
                continue
            else:
                logging.error(f"Failed to download {file_key}: {e}")
    
    return sku, False, None

def sync_skus(config: SyncConfig, sku_list: List[str], file_extensions: List[str] = ['.pdf']) -> List[Tuple[str, bool]]:
    """Sync multiple SKUs from S3.
    
    Args:
        config: Sync configuration
        sku_list: List of SKUs to sync
        file_extensions: List of file extensions to try (default: ['.pdf'])
    
    Returns:
        List of (sku, success) tuples
    """
    s3_client = boto3.client('s3')
    results = []
    completed = 0
    total = len(sku_list)
    
    # Ensure download directory exists
    Path(config.local_download_path).mkdir(parents=True, exist_ok=True)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        # Submit all tasks
        future_to_sku = {executor.submit(download_sku_file, s3_client, config, sku, file_extensions): sku 
                         for sku in sku_list}
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_sku):
            sku = future_to_sku[future]
            try:
                sku_result, success, file_path = future.result()
                results.append((sku_result, success))
                completed += 1
                
                # Progress logging every 10 items or at completion
                if completed % 10 == 0 or completed == total:
                    logging.info(f"Progress: {completed}/{total} SKUs processed")
                    
            except Exception as e:
                logging.error(f"Error processing SKU {sku}: {e}")
                results.append((sku, False))
                completed += 1
    
    return results
