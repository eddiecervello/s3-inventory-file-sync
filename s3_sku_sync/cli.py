import argparse
import sys
import logging
import os
import re
from pathlib import Path
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
    
    # Security validation for arguments
    try:
        # Validate bucket name
        if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', args.bucket.lower()):
            parser.error(f"Invalid S3 bucket name format: {args.bucket}")
        
        # Validate Excel file path
        excel_path = Path(args.excel).resolve()
        if not excel_path.exists():
            parser.error(f"Excel file does not exist: {args.excel}")
        if not excel_path.is_file():
            parser.error(f"Excel path is not a file: {args.excel}")
        if excel_path.suffix.lower() not in ['.xlsx', '.xls']:
            parser.error(f"Excel file must have .xlsx or .xls extension: {args.excel}")
        
        # Validate local download path
        local_path = Path(args.local).resolve()
        try:
            # Try to create the directory if it doesn't exist
            local_path.mkdir(parents=True, exist_ok=True)
            # Check if we can write to it
            if not os.access(local_path, os.W_OK):
                parser.error(f"Cannot write to local directory: {args.local}")
        except Exception as e:
            parser.error(f"Invalid local directory path: {e}")
        
        # Validate S3 prefix (if provided)
        if args.prefix:
            # Basic validation for S3 prefix
            if '..' in args.prefix or args.prefix.startswith('/'):
                parser.error(f"Invalid S3 prefix: {args.prefix}")
            if not re.match(r'^[a-zA-Z0-9!_.*()/-]*$', args.prefix):
                parser.error(f"S3 prefix contains invalid characters: {args.prefix}")
        
        # Validate max workers
        if args.max_workers < 1 or args.max_workers > 50:
            parser.error("Max workers must be between 1 and 50")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if args.log_level.upper() not in valid_log_levels:
            parser.error(f"Invalid log level. Must be one of: {valid_log_levels}")
            
    except Exception as e:
        parser.error(f"Validation error: {e}")
    
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
    
    # Parse and validate file extensions
    try:
        file_extensions = [ext.strip() for ext in args.file_extensions.split(',')]
        for ext in file_extensions:
            if not re.match(r'^\.[a-zA-Z0-9]+$', ext):
                logging.error(f"Invalid file extension format: {ext}")
                sys.exit(1)
            if len(ext) > 10:  # Reasonable limit
                logging.error(f"File extension too long: {ext}")
                sys.exit(1)
    except Exception as e:
        logging.error(f"Error parsing file extensions: {e}")
        sys.exit(1)
    
    # Handle dry-run mode
    if args.dry_run:
        logging.info("DRY RUN MODE - No files will be downloaded")
        logging.info(f"Would sync {len(sku_list)} SKUs from s3://{config.bucket_name}/{config.s3_prefix} to {config.local_download_path}")
        logging.info(f"File extensions: {file_extensions}")
        logging.info(f"Configuration validated successfully")
        sys.exit(0)
    
    results = sync_skus(config, sku_list, file_extensions)
    failed = [sku for sku, ok in results if not ok]
    if failed:
        logging.warning(f"{len(failed)} SKUs failed to sync: {failed}")
    else:
        logging.info("All SKUs synced successfully.")

if __name__ == "__main__":
    main()
