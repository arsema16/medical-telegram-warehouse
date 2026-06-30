"""
Pytest configuration and fixtures for the test suite.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ['TELEGRAM_API_ID'] = '12345'
    os.environ['TELEGRAM_API_HASH'] = 'test_hash'
    os.environ['TELEGRAM_PHONE'] = '+1234567890'
    os.environ['TELEGRAM_CHANNELS'] = 'test_channel1,test_channel2'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_PORT'] = '5432'
    os.environ['DB_USER'] = 'test_user'
    os.environ['DB_PASSWORD'] = 'test_password'
    os.environ['DB_NAME'] = 'test_db'
    yield


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory."""
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def mock_telegram_client():
    """Mock Telegram client for testing."""
    client = Mock()
    client.start = Mock()
    client.iter_messages = Mock()
    client.download_media = Mock()
    return client


@pytest.fixture
def sample_telegram_message():
    """Create a sample Telegram message object."""
    message = Mock()
    message.id = 12345
    message.date = "2026-06-28T12:00:00"
    message.text = "Sample message text"
    message.media = None
    message.views = 100
    message.forwards = 50
    message.replies = {'replies': 25}
    return message


@pytest.fixture
def sample_json_message():
    """Create a sample JSON message dictionary."""
    return {
        'message_id': 12345,
        'channel_name': 'test_channel',
        'message_date': '2026-06-28T12:00:00',
        'message_text': 'Sample message text',
        'has_media': False,
        'image_path': None,
        'views': 100,
        'forwards': 50,
        'replies': 25
    }


@pytest.fixture
def sample_channel_data():
    """Create sample channel data."""
    return [
        {
            'message_id': 1001,
            'channel_name': 'chemed',
            'message_date': '2026-06-28T10:00:00',
            'message_text': 'Product A available now! Price: 500 birr',
            'has_media': True,
            'image_path': 'data/raw/images/chemed/1001.jpg',
            'views': 150,
            'forwards': 20,
            'replies': 10
        },
        {
            'message_id': 1002,
            'channel_name': 'lobelia',
            'message_date': '2026-06-28T11:00:00',
            'message_text': 'New cosmetic products',
            'has_media': True,
            'image_path': 'data/raw/images/lobelia/1002.jpg',
            'views': 200,
            'forwards': 30,
            'replies': 15
        },
        {
            'message_id': 1003,
            'channel_name': 'tikvah',
            'message_date': '2026-06-28T12:00:00',
            'message_text': 'Pharmaceutical products in stock',
            'has_media': False,
            'image_path': None,
            'views': 100,
            'forwards': 10,
            'replies': 5
        }
    ]


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    connection = Mock()
    cursor = Mock()
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection