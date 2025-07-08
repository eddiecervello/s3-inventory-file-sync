import os
import logging
import boto3
from botocore.exceptions import NoCredentialsError
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# AWS credentials should be stored in environment variables or AWS credentials file
# Alternatively, you can explicitly pass your credentials as arguments to the boto3 client,
# but it is not recommended to hardcode sensitive information in your scripts.

# Initialize a session using Amazon S3
session = boto3.session.Session()
s3 = session.client('s3')

# The name of your S3 bucket and local download path
BUCKET_NAME = 'your-bucket-name'  # replace with your bucket name
LOCAL_DOWNLOAD_PATH = 'path/to/your/download/directory'  # replace with your local path

# Function to download files from S3
def download_files_from_s3(sku_list):
    for sku in sku_list:
        try:
            # Define the S3 object key. If your filenames differ, adjust the key accordingly.
            file_key = f'path/to/sku/{sku}.pdf'  # replace with your file path structure

            # The local path to which the file should be downloaded
            local_file_path = os.path.join(LOCAL_DOWNLOAD_PATH, f'{sku}.pdf')

            # Download the file
            s3.download_file(BUCKET_NAME, file_key, local_file_path)
            logging.info(f"File {file_key} downloaded to {local_file_path}")
        except NoCredentialsError:
            logging.error("AWS credentials not available")
            return
        except Exception as e:
            logging.error(f"Error downloading {file_key}: {e}")

# Read SKUs from an Excel file
def get_skus_from_excel(excel_path):
    try:
        df = pd.read_excel(excel_path)
        return df['SKU'].tolist()  # Replace 'SKU' with the actual column name in your Excel file
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return []

# Main execution
if __name__ == "__main__":
    # IMPORTANT: This is a legacy script. Use s3_sku_sync.py instead for better performance and features.
    logging.warning("This is a legacy script. Consider using 's3_sku_sync.py' for better performance and features.")
    
    # Path to your Excel file
    excel_file_path = 'path/to/your/excel/file.xlsx'  # replace with your Excel file path
    
    # Get SKUs from Excel
    sku_list = get_skus_from_excel(excel_file_path)
    
    if sku_list:
        logging.info(f"Found {len(sku_list)} SKUs to download")
        
        # Create download directory if it doesn't exist
        os.makedirs(LOCAL_DOWNLOAD_PATH, exist_ok=True)
        
        # Download files
        download_files_from_s3(sku_list)
        logging.info("Download process completed")
    else:
        logging.error("No SKUs found in Excel file")
