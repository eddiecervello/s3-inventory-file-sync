import pandas as pd
import re
from typing import List
from pathlib import Path

def get_skus_from_excel(excel_path: str, column_name: str = 'SKU') -> List[str]:
    """Read SKUs from Excel file with security validation.
    
    Args:
        excel_path: Path to Excel file
        column_name: Name of column containing SKUs (default: 'SKU')
    
    Returns:
        List of validated SKU strings
    
    Raises:
        ValueError: If column not found, file invalid, or SKUs contain invalid characters
        FileNotFoundError: If Excel file doesn't exist
        PermissionError: If file cannot be read
    """
    # Validate file path
    try:
        file_path = Path(excel_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {excel_path}")
        if file_path.suffix.lower() not in ['.xlsx', '.xls']:
            raise ValueError(f"File must be Excel format (.xlsx or .xls): {excel_path}")
        
        # Check file size (limit to 50MB for security)
        if file_path.stat().st_size > 50 * 1024 * 1024:
            raise ValueError(f"Excel file too large (max 50MB): {excel_path}")
            
    except (OSError, PermissionError) as e:
        raise PermissionError(f"Cannot access Excel file: {e}")
    
    # Validate column name
    if not column_name or not column_name.strip():
        raise ValueError("Column name cannot be empty")
    
    # Validate column name format (prevent injection)
    if not re.match(r'^[a-zA-Z0-9 _#-]+$', column_name):
        raise ValueError(f"Column name contains invalid characters: {column_name}")
    
    try:
        # Read Excel file with safety limits
        df = pd.read_excel(
            file_path, 
            nrows=10000,  # Limit rows for security
            engine='openpyxl' if file_path.suffix.lower() == '.xlsx' else 'xlrd'
        )
        
        # Check if DataFrame is empty
        if df.empty:
            raise ValueError("Excel file is empty")
            
        # Validate column exists
        if column_name not in df.columns:
            available_cols = [col for col in df.columns if isinstance(col, str) and len(col) < 100]
            raise ValueError(f"Column '{column_name}' not found in Excel file. Available columns: {available_cols}")
        
        # Extract and validate SKUs
        sku_series = df[column_name].dropna().astype(str).str.strip()
        
        # Filter out empty strings
        sku_series = sku_series[sku_series != '']
        
        if sku_series.empty:
            raise ValueError(f"No valid SKUs found in column '{column_name}'")
        
        # Validate each SKU
        valid_skus = []
        invalid_count = 0
        
        for sku in sku_series.tolist():
            # Basic SKU validation
            if len(sku) > 100:
                invalid_count += 1
                continue
                
            # Check for path traversal and dangerous characters
            if '..' in sku or '/' in sku or '\\' in sku:
                invalid_count += 1
                continue
                
            # Only allow alphanumeric, hyphens, underscores, and periods
            if not re.match(r'^[a-zA-Z0-9._-]+$', sku):
                invalid_count += 1
                continue
                
            valid_skus.append(sku)
        
        if invalid_count > 0:
            print(f"Warning: Skipped {invalid_count} SKUs with invalid characters")
        
        if not valid_skus:
            raise ValueError("No valid SKUs found after validation")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skus = []
        for sku in valid_skus:
            if sku not in seen:
                seen.add(sku)
                unique_skus.append(sku)
        
        # Limit number of SKUs for security
        if len(unique_skus) > 10000:
            raise ValueError(f"Too many SKUs (max 10000): {len(unique_skus)}")
        
        return unique_skus
        
    except pd.errors.EmptyDataError:
        raise ValueError("Excel file contains no data")
    except pd.errors.ParserError as e:
        raise ValueError(f"Cannot parse Excel file: {e}")
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")
