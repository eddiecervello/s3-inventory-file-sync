import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from s3_sku_sync.config import SyncConfig
from s3_sku_sync.s3_sync import download_sku_file, sync_skus


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return SyncConfig(
        bucket_name='test-bucket',
        local_download_path='/tmp/test',
        sku_excel_path='test.xlsx',
        s3_prefix='skus/',
        max_workers=2,
        log_level='INFO'
    )


def test_download_sku_file_success(mock_config):
    """Test successful file download."""
    mock_s3_client = Mock()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config.local_download_path = tmpdir
        
        sku, success, file_path = download_sku_file(
            mock_s3_client, mock_config, 'SKU001'
        )
        
        assert sku == 'SKU001'
        assert success is True
        assert file_path.endswith('SKU001.pdf')
        mock_s3_client.download_file.assert_called_once_with(
            'test-bucket', 'skus/SKU001.pdf', os.path.join(tmpdir, 'SKU001.pdf')
        )


def test_download_sku_file_already_exists(mock_config):
    """Test skipping download when file exists."""
    mock_s3_client = Mock()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config.local_download_path = tmpdir
        # Create existing file
        existing_file = os.path.join(tmpdir, 'SKU001.pdf')
        with open(existing_file, 'w') as f:
            f.write('test')
        
        sku, success, file_path = download_sku_file(
            mock_s3_client, mock_config, 'SKU001'
        )
        
        assert sku == 'SKU001'
        assert success is True
        assert file_path == existing_file
        # Should not attempt download
        mock_s3_client.download_file.assert_not_called()


def test_download_sku_file_not_found(mock_config):
    """Test handling of missing file."""
    mock_s3_client = Mock()
    error_response = {'Error': {'Code': 'NoSuchKey'}}
    mock_s3_client.download_file.side_effect = ClientError(error_response, 'GetObject')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config.local_download_path = tmpdir
        
        sku, success, file_path = download_sku_file(
            mock_s3_client, mock_config, 'SKU001'
        )
        
        assert sku == 'SKU001'
        assert success is False
        assert file_path is None


def test_download_sku_file_multiple_extensions(mock_config):
    """Test trying multiple file extensions."""
    mock_s3_client = Mock()
    
    # First extension fails, second succeeds
    error_response = {'Error': {'Code': 'NoSuchKey'}}
    mock_s3_client.download_file.side_effect = [
        ClientError(error_response, 'GetObject'),
        None  # Success on second call
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config.local_download_path = tmpdir
        
        sku, success, file_path = download_sku_file(
            mock_s3_client, mock_config, 'SKU001', ['.pdf', '.txt']
        )
        
        assert sku == 'SKU001'
        assert success is True
        assert file_path.endswith('SKU001.txt')
        assert mock_s3_client.download_file.call_count == 2


@patch('s3_sku_sync.s3_sync.boto3.client')
def test_sync_skus_creates_directory(mock_boto_client, mock_config):
    """Test that sync_skus creates the download directory."""
    mock_s3_client = Mock()
    mock_boto_client.return_value = mock_s3_client
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use a subdirectory that doesn't exist
        mock_config.local_download_path = os.path.join(tmpdir, 'new_dir')
        
        results = sync_skus(mock_config, ['SKU001'])
        
        # Directory should be created
        assert os.path.exists(mock_config.local_download_path)


@patch('s3_sku_sync.s3_sync.boto3.client')
@patch('s3_sku_sync.s3_sync.download_sku_file')
def test_sync_skus_batch_processing(mock_download, mock_boto_client, mock_config):
    """Test batch processing of multiple SKUs."""
    mock_s3_client = Mock()
    mock_boto_client.return_value = mock_s3_client
    
    # Mock successful downloads
    mock_download.side_effect = [
        ('SKU001', True, '/tmp/SKU001.pdf'),
        ('SKU002', True, '/tmp/SKU002.pdf'),
        ('SKU003', False, None),
    ]
    
    results = sync_skus(mock_config, ['SKU001', 'SKU002', 'SKU003'])
    
    assert len(results) == 3
    assert ('SKU001', True) in results
    assert ('SKU002', True) in results
    assert ('SKU003', False) in results