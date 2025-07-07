import argparse
import sys
import logging
from .config import SyncConfig
from .excel_utils import get_skus_from_excel
from .s3_sync import sync_skus
from .logging_utils import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Sync SKU files from S3 bucket.")
    parser.add_argument('--config', type=str, required=True, help='Path to config YAML/JSON file or pass as CLI args')
    parser.add_argument('--bucket', type=str, help='S3 bucket name')
    parser.add_argument('--excel', type=str, help='Path to Excel file with SKUs')
    parser.add_argument('--local', type=str, help='Local download directory')
    parser.add_argument('--prefix', type=str, default='', help='S3 prefix for SKU files')
    parser.add_argument('--max-workers', type=int, default=8, help='Max concurrent downloads')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    args = parser.parse_args()

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
    try:
        sku_list = get_skus_from_excel(config.sku_excel_path)
    except Exception as e:
        logging.error(f"Failed to read SKUs: {e}")
        sys.exit(1)
    results = sync_skus(config, sku_list)
    failed = [sku for sku, ok in results if not ok]
    if failed:
        logging.warning(f"{len(failed)} SKUs failed to sync: {failed}")
    else:
        logging.info("All SKUs synced successfully.")

if __name__ == "__main__":
    main()
