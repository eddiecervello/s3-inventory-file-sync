import pytest
import pandas as pd
import tempfile
import os
from s3_sku_sync.excel_utils import get_skus_from_excel


def test_get_skus_from_excel_valid():
    """Test reading SKUs from a valid Excel file."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df = pd.DataFrame({
            'SKU': ['SKU001', 'SKU002', 'SKU003', None, 'SKU004'],
            'Description': ['Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5']
        })
        df.to_excel(f.name, index=False)
        temp_path = f.name
    
    try:
        skus = get_skus_from_excel(temp_path)
        assert len(skus) == 4  # Should skip None value
        assert skus == ['SKU001', 'SKU002', 'SKU003', 'SKU004']
    finally:
        os.unlink(temp_path)


def test_get_skus_from_excel_custom_column():
    """Test reading SKUs from a custom column."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df = pd.DataFrame({
            'ProductCode': ['PC001', 'PC002', 'PC003'],
            'Description': ['Item 1', 'Item 2', 'Item 3']
        })
        df.to_excel(f.name, index=False)
        temp_path = f.name
    
    try:
        skus = get_skus_from_excel(temp_path, column_name='ProductCode')
        assert len(skus) == 3
        assert skus == ['PC001', 'PC002', 'PC003']
    finally:
        os.unlink(temp_path)


def test_get_skus_from_excel_missing_column():
    """Test error handling for missing column."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df = pd.DataFrame({
            'ProductCode': ['PC001', 'PC002'],
            'Description': ['Item 1', 'Item 2']
        })
        df.to_excel(f.name, index=False)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError) as excinfo:
            get_skus_from_excel(temp_path)  # Default 'SKU' column doesn't exist
        assert "Column 'SKU' not found" in str(excinfo.value)
    finally:
        os.unlink(temp_path)


def test_get_skus_from_excel_strips_whitespace():
    """Test that SKUs have whitespace stripped."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df = pd.DataFrame({
            'SKU': [' SKU001 ', 'SKU002\n', '\tSKU003', 'SKU004']
        })
        df.to_excel(f.name, index=False)
        temp_path = f.name
    
    try:
        skus = get_skus_from_excel(temp_path)
        assert skus == ['SKU001', 'SKU002', 'SKU003', 'SKU004']
    finally:
        os.unlink(temp_path)