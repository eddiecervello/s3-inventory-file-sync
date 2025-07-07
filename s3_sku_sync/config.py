from pydantic import BaseModel, Field
from typing import Optional

class SyncConfig(BaseModel):
    bucket_name: str = Field(..., description="S3 bucket name")
    local_download_path: str = Field(..., description="Local directory for downloads")
    sku_excel_path: str = Field(..., description="Path to Excel file with SKUs")
    s3_prefix: Optional[str] = Field('', description="S3 prefix for SKU files")
    max_workers: int = Field(8, description="Max concurrent downloads")
    log_level: str = Field('INFO', description="Logging level")
