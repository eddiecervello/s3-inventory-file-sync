import pandas as pd
from typing import List

def get_skus_from_excel(excel_path: str, column_name: str = 'SKU') -> List[str]:
    """Read SKUs from Excel file.
    
    Args:
        excel_path: Path to Excel file
        column_name: Name of column containing SKUs (default: 'SKU')
    
    Returns:
        List of SKU strings
    
    Raises:
        ValueError: If column not found in Excel file
    """
    df = pd.read_excel(excel_path)
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in Excel file. Available columns: {list(df.columns)}")
    return df[column_name].dropna().astype(str).str.strip().tolist()
