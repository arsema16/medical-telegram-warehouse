"""
Unit tests for data loader functionality.
"""

import os
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import DataLoader


@pytest.fixture
def mock_db_env(monkeypatch):
    """Mock database environment variables."""
    monkeypatch.setenv('DB_HOST', 'localhost')
    monkeypatch.setenv('DB_PORT', '5432')
    monkeypatch.setenv('DB_USER', 'test_user')
    monkeypatch.setenv('DB_PASSWORD', 'test_password')
    monkeypatch.setenv('DB_NAME', 'test_db')


@pytest.fixture
def data_loader(mock_db_env, tmp_path):
    """Create a DataLoader instance with temporary data directory."""
    loader = DataLoader()
    loader.data_dir = tmp_path / 'data/raw/telegram_messages'
    loader.data_dir.mkdir(parents=True, exist_ok=True)
    return loader


@pytest.fixture
def sample_messages():
    """Create sample messages for testing."""
    return [
        {
            'message_id': 1001,
            'channel_name': 'chemed',
            'message_date': datetime.now().isoformat(),
            'message_text': 'Test message 1',
            'has_media': False,
            'image_path': None,
            'views': 100,
            'forwards': 10,
            'replies': 5
        },
        {
            'message_id': 1002,
            'channel_name': 'lobelia',
            'message_date': datetime.now().isoformat(),
            'message_text': 'Test message 2 with image',
            'has_media': True,
            'image_path': '/path/to/image.jpg',
            'views': 200,
            'forwards': 20,
            'replies': 15
        }
    ]


class TestDataLoader:
    """Test suite for DataLoader class."""

    def test_init(self, mock_db_env):
        """Test DataLoader initialization."""
        loader = DataLoader()
        assert loader.conn_params['host'] == 'localhost'
        assert loader.conn_params['database'] == 'test_db'
        assert loader.conn_params['user'] == 'test_user'
        assert loader.data_dir == Path('data/raw/telegram_messages')

    @patch('psycopg2.connect')
    def test_connect(self, mock_connect, data_loader):
        """Test database connection."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        data_loader.connect()

        mock_connect.assert_called_once_with(**data_loader.conn_params)
        assert data_loader.connection == mock_connection

    @patch('psycopg2.connect')
    def test_connect_failure(self, mock_connect, data_loader):
        """Test database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            data_loader.connect()

    @patch('psycopg2.connect')
def test_create_raw_table(self, mock_connect, data_loader):
    """Test raw table creation."""
    # Create a mock connection with proper context manager support
    mock_connection = Mock()
    mock_cursor = Mock()
    
    # Setup the context manager properly
    mock_connection.__enter__ = Mock(return_value=mock_connection)
    mock_connection.__exit__ = Mock(return_value=False)
    mock_connection.cursor.return_value = mock_cursor
    
    mock_connect.return_value = mock_connection
    
    data_loader.connection = mock_connection
    data_loader.create_raw_table()
    
    # Check that execute was called with SQL containing CREATE TABLE
    assert mock_cursor.execute.called
    sql_call = mock_cursor.execute.call_args[0][0]
    assert 'CREATE SCHEMA' in sql_call
    assert 'CREATE TABLE' in sql_call
    assert 'raw.telegram_messages' in sql_call
    mock_connection.commit.assert_called_once()

    def test_load_json_files(self, data_loader, sample_messages, tmp_path):
        """Test loading JSON files."""
        # Create test JSON files
        date_str = datetime.now().date().isoformat()
        date_dir = data_loader.data_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        file_path = date_dir / 'chemed.json'
        with open(file_path, 'w') as f:
            json.dump([sample_messages[0]], f)

        # Load data
        messages = data_loader.load_json_files()

        assert len(messages) == 1
        assert messages[0]['message_id'] == 1001
        assert messages[0]['channel_name'] == 'chemed'

    def test_load_json_files_with_date_filter(self, data_loader, tmp_path):
        """Test loading JSON files with date filter."""
        # Create files for different dates
        date1 = '2026-06-24'
        date2 = '2026-06-25'

        for date_str in [date1, date2]:
            date_dir = data_loader.data_dir / date_str
            date_dir.mkdir(parents=True, exist_ok=True)
            file_path = date_dir / 'channel.json'
            with open(file_path, 'w') as f:
                json.dump([
                    {'message_id': int(date_str.replace('-', '')),
                     'channel_name': 'test'}
                ], f)

        # Load only date1
        messages = data_loader.load_json_files(date_filter=date1)

        assert len(messages) == 1
        assert messages[0]['message_id'] == 20260624

    def test_load_json_files_empty_directory(self, data_loader):
        """Test loading from empty directory."""
        messages = data_loader.load_json_files()
        assert messages == []

    def test_load_json_files_invalid_json(self, data_loader, tmp_path):
        """Test loading invalid JSON file."""
        date_str = datetime.now().date().isoformat()
        date_dir = data_loader.data_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        file_path = date_dir / 'invalid.json'
        with open(file_path, 'w') as f:
            f.write('invalid json {')

        messages = data_loader.load_json_files()
        assert messages == []  # Should handle error gracefully

    @patch('src.data_loader.execute_values')
    @patch('psycopg2.connect')
    def test_load_to_database(self, mock_connect, mock_execute_values,
                              data_loader, sample_messages):
        """Test loading data to database."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        data_loader.connection = mock_connection

        count = data_loader.load_to_database(sample_messages)

        assert count == 2
        mock_execute_values.assert_called_once()
        mock_connection.commit.assert_called_once()

    @patch('psycopg2.connect')
    def test_load_to_database_empty(self, mock_connect, data_loader):
        """Test loading empty list."""
        count = data_loader.load_to_database([])
        assert count == 0

    @patch('psycopg2.connect')
    def test_load_to_database_error(self, mock_connect, data_loader,
                                    sample_messages):
        """Test handling database error during load."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        data_loader.connection = mock_connection

        with pytest.raises(Exception, match="Database error"):
            data_loader.load_to_database(sample_messages)

        mock_connection.rollback.assert_called_once()

    @patch('src.data_loader.DataLoader.connect')
    @patch('src.data_loader.DataLoader.load_json_files')
    @patch('src.data_loader.DataLoader.load_to_database')
    @patch('src.data_loader.DataLoader.close')
    def test_load_all(self, mock_close, mock_load_to_db, mock_load_json,
                      mock_connect, data_loader):
        """Test load_all workflow."""
        mock_load_json.return_value = [{'message_id': 1}]
        mock_load_to_db.return_value = 1

        count = data_loader.load_all()

        mock_connect.assert_called_once()
        mock_load_json.assert_called_once()
        mock_load_to_db.assert_called_once()
        mock_close.assert_called_once()
        assert count == 1

    def test_close_connection(self, data_loader):
        """Test closing database connection."""
        mock_connection = Mock()
        data_loader.connection = mock_connection

        data_loader.close()
        mock_connection.close.assert_called_once()

        # Test closing when connection is None
        data_loader.connection = None
        data_loader.close()  # Should not raise


class TestDataLoaderIntegration:
    """Integration tests for DataLoader (requires database)."""

    @pytest.mark.skip(reason="Requires actual database connection")
    def test_real_load(self):
        """Test loading with real database (skipped by default)."""
        pass