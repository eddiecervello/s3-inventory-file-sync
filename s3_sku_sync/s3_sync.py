import os
import logging
import concurrent.futures
import boto3
from botocore.exceptions import ClientError
from .config import SyncConfig

def download_sku_file(s3_client, config: SyncConfig, sku: str):
    file_key = f"{config.s3_prefix}{sku}.pdf"
    local_file_path = os.path.join(config.local_download_path, f"{sku}.pdf")
    try:
        s3_client.download_file(config.bucket_name, file_key, local_file_path)
        logging.info(f"Downloaded {file_key} to {local_file_path}")
        return sku, True
    except ClientError as e:
        logging.error(f"Failed to download {file_key}: {e}")
        return sku, False

def sync_skus(config: SyncConfig, sku_list: list[str]):
    s3_client = boto3.client('s3')
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        futures = {executor.submit(download_sku_file, s3_client, config, sku): sku for sku in sku_list}
        results = []
        for future in concurrent.futures.as_completed(futures):
            sku, success = future.result()
            results.append((sku, success))
    return results
