# AWS S3 SKU File Sync

This script automates the process of downloading files associated with a list of SKUs from an AWS S3 bucket to a local directory. It is designed to handle the synchronization of product files, ensuring that a local copy of the required files is always up-to-date.

## Features

- Reads SKUs from an Excel file and searches for corresponding files in an S3 bucket.
- Downloads found files to a local directory, maintaining the SKU structure.
- Skips empty folders and logs SKUs with no files found.
- Provides detailed logs for tracking and verification purposes.

## Prerequisites

- AWS account with S3 read access.
- Python 3.6 or higher.
- `boto3` and `pandas` libraries installed.

## Installation

Clone the repository to your local machine:

```bash
git clone https://github.com/<your-username>/s3-sku-file-sync.git
cd s3-sku-file-sync
```

Install the required Python packages:

```pip install -r requirements.txt```

## Configuration

Set up your AWS credentials by configuring the AWS CLI or by exporting them as environment variables:

```bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_SESSION_TOKEN='your_session_token'  # if applicable
```

## Usage
1. Place your 'SKU-list.xlsx' file in the root directory of the script.
2. Run the script:
   
```python s3_sku_sync.py```

3. Check the s3_download.log and not_found_skus.txt files for the results.

## Logs

- `s3_download.log`: Contains detailed information about the download process.
- `not_found_skus.txt`: Lists SKUs that were not found in the S3 bucket.
