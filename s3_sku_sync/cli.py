import argparse
import sys
import logging
import os
from .config import SyncConfig
from .excel_utils import get_skus_from_excel
from .s3_sync import sync_skus
from .logging_utils import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Sync SKU files from S3 bucket.")
    parser.add_argument('--config', type=str, help='Path to config YAML/JSON file (optional)')
    parser.add_argument('--bucket', type=str, help='S3 bucket name')
    parser.add_argument('--excel', type=str, help='Path to Excel file with SKUs')
    parser.add_argument('--local', type=str, help='Local download directory')
    parser.add_argument('--prefix', type=str, default='', help='S3 prefix for SKU files')
    parser.add_argument('--max-workers', type=int, default=8, help='Max concurrent downloads')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    parser.add_argument('--file-extensions', type=str, default='.pdf', help='Comma-separated file extensions to download (e.g., ".pdf,.txt")')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without actually downloading')
    args = parser.parse_args()

    # Validate required arguments
    if not all([args.bucket, args.excel, args.local]):
        parser.error("--bucket, --excel, and --local are required arguments")
    
    # Build config from args (YAML/JSON config support can be added later)
    config = SyncConfig(
        bucket_name=args.bucket,
        local_download_path=args.local,
        sku_excel_path=args.excel,
        s3_prefix=args.prefix,
        max_workers=args.max_workers,
        log_level=args.log_level
    )
    setup_logging(config.log_level)
    
    # Ensure local download directory exists
    os.makedirs(config.local_download_path, exist_ok=True)
    
    try:
        sku_list = get_skus_from_excel(config.sku_excel_path)
        if not sku_list:
            logging.error("No SKUs found in Excel file")
            sys.exit(1)
        logging.info(f"Found {len(sku_list)} SKUs to sync")
    except Exception as e:
        logging.error(f"Failed to read SKUs: {e}")
        sys.exit(1)
    
    # Parse file extensions
    file_extensions = [ext.strip() for ext in args.file_extensions.split(',')]
    
    # Handle dry-run mode
    if args.dry_run:
        logging.info("DRY RUN MODE - No files will be downloaded")
        logging.info(f"Would sync {len(sku_list)} SKUs from s3://{config.bucket_name}/{config.s3_prefix} to {config.local_download_path}")
        logging.info(f"File extensions: {file_extensions}")
        sys.exit(0)
    
    results = sync_skus(config, sku_list, file_extensions)
    failed = [sku for sku, ok in results if not ok]
    if failed:
        logging.warning(f"{len(failed)} SKUs failed to sync: {failed}")
    else:
        logging.info("All SKUs synced successfully.")

if __name__ == "__main__":
    main()
