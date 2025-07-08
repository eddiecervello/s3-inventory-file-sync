# AWS S3 SKU File Sync

> **v2.0.0: Now a modular, concurrent, production-grade sync tool!**

This package automates the process of downloading files associated with a list of SKUs from an AWS S3 bucket to a local directory, with robust concurrency, logging, and testability.

## Features

- Reads SKUs from an Excel file and searches for corresponding files in an S3 bucket.
- Concurrent downloads (configurable workers) for high throughput.
- Strict typing, pydantic config, and JSON-line logging.
- CLI entry point: `python s3_sku_sync.py` (zero-downtime upgrade)
- Ready for CI/CD, test coverage, and observability.
- **NEW**: Configurable file extensions (not just PDFs)
- **NEW**: Dry-run mode for safe testing
- **NEW**: Automatic directory creation
- **NEW**: Skip existing files to avoid re-downloads
- **NEW**: Progress tracking for large batches
- **NEW**: Better error handling with specific error codes

## Prerequisites

- AWS account with S3 read access.
- Python 3.12 or higher.
- `boto3` >= 1.34, `pandas` >= 2.2, `pydantic` >= 2.0

## Installation

Clone the repository to your local machine:

```bash
git clone https://github.com/<your-username>/s3-sku-file-sync.git
cd s3-sku-file-sync
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Configuration

Set up your AWS credentials by configuring the AWS CLI or by exporting them as environment variables:

```bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_SESSION_TOKEN='your_session_token'  # if applicable
```

## Usage

1. Place your Excel file (e.g., `SKU-list.xlsx`) in the repo root.
2. Run the sync:

```bash
python s3_sku_sync.py --bucket <bucket> --excel SKU-list.xlsx --local ./downloads
```

Optional flags:
- `--prefix <s3-prefix>` - S3 prefix for SKU files
- `--max-workers 16` - Number of concurrent downloads (default: 8)
- `--log-level DEBUG` - Logging level (default: INFO)
- `--file-extensions .pdf,.txt` - Comma-separated file extensions to try (default: .pdf)
- `--dry-run` - Show what would be downloaded without actually downloading
- `--config <path>` - Path to config file (optional, for future use)

## Architecture

![Architecture Diagram](docs/architecture.png)

- `s3_sku_sync/` — modular package (config, logging, S3, Excel utils)
- `s3_sku_sync.py` — CLI entry point

## Logs & Observability

- JSON-line logs to stdout (INFO milestones, DEBUG for steps)
- Extendable for Grafana dashboards and CI/CD metrics
- Progress tracking logged every 10 items
- Detailed error codes for troubleshooting

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes.

---

## Testing

Run the test suite:

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=s3_sku_sync --cov-report=term-missing
```

## Troubleshooting

- **No SKUs found**: Check that your Excel file has a column named 'SKU' (case-sensitive)
- **All downloads fail**: Verify AWS credentials and bucket permissions
- **404 errors**: Check the S3 prefix and file extensions match your bucket structure
- **Slow downloads**: Increase `--max-workers` based on your network and CPU capacity

For full docs, see the [mkdocs site](docs/).
