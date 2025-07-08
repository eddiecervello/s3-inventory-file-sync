from pydantic import BaseModel, Field, validator
from typing import Optional
import re
from pathlib import Path

class SyncConfig(BaseModel):
    bucket_name: str = Field(..., description="S3 bucket name")
    local_download_path: str = Field(..., description="Local directory for downloads")
    sku_excel_path: str = Field(..., description="Path to Excel file with SKUs")
    s3_prefix: Optional[str] = Field('', description="S3 prefix for SKU files")
    max_workers: int = Field(8, description="Max concurrent downloads", ge=1, le=50)
    log_level: str = Field('INFO', description="Logging level")
    
    @validator('bucket_name')
    def validate_bucket_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Bucket name cannot be empty')
        v = v.strip()
        if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', v.lower()):
            raise ValueError(f'Invalid S3 bucket name format: {v}')
        if len(v) < 3 or len(v) > 63:
            raise ValueError(f'Bucket name must be between 3 and 63 characters: {v}')
        return v
    
    @validator('local_download_path')
    def validate_local_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Local download path cannot be empty')
        try:
            path = Path(v).resolve()
            # Don't create the directory here, just validate the path format
            return str(path)
        except Exception as e:
            raise ValueError(f'Invalid local download path: {e}')
    
    @validator('sku_excel_path')
    def validate_excel_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Excel file path cannot be empty')
        try:
            path = Path(v).resolve()
            if not path.exists():
                raise ValueError(f'Excel file does not exist: {v}')
            if not path.is_file():
                raise ValueError(f'Excel path is not a file: {v}')
            if path.suffix.lower() not in ['.xlsx', '.xls']:
                raise ValueError(f'Excel file must have .xlsx or .xls extension: {v}')
            return str(path)
        except Exception as e:
            raise ValueError(f'Invalid Excel file path: {e}')
    
    @validator('s3_prefix')
    def validate_s3_prefix(cls, v):
        if v is None:
            return ''
        v = v.strip()
        if v and not re.match(r'^[a-zA-Z0-9!_.*()/-]*$', v):
            raise ValueError(f'S3 prefix contains invalid characters: {v}')
        if '..' in v:
            raise ValueError(f'S3 prefix cannot contain "..": {v}')
        if len(v) > 1024:
            raise ValueError(f'S3 prefix too long (max 1024 chars): {v}')
        # Ensure prefix ends with / if not empty
        if v and not v.endswith('/'):
            v += '/'
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        if not v or not v.strip():
            raise ValueError('Log level cannot be empty')
        v = v.strip().upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in valid_levels:
            raise ValueError(f'Invalid log level. Must be one of: {valid_levels}')
        return v
