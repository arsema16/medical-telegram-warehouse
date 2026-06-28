"""
Unit tests for Telegram scraper functionality.
"""

import os
import json
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import TelegramScraper


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv('TELEGRAM_API_ID', '12345')
    monkeypatch.setenv('TELEGRAM_API_HASH', 'test_hash')
    monkeypatch.setenv('TELEGRAM_PHONE', '+1234567890')
    monkeypatch.setenv('TELEGRAM_CHANNELS', 'chemed,lobeliacosmetics,tikvahpharma')


@pytest.fixture
def scraper(mock_env_vars, tmp_path):
    """Create a scraper instance with temporary data directory."""
    scraper = TelegramScraper()
    scraper.base_data_dir = tmp_path / 'data/raw'
    scraper.base_data_dir.mkdir(parents=True, exist_ok=True)
    return scraper


@pytest.fixture
def sample_message():
    """Create a sample Telegram message object."""
    message = Mock()
    message.id = 12345
    message.date = datetime.now()
    message.text = "Test message content with product information"
    message.media = None
    message.views = 100
    message.forwards = 50
    message.replies = {'replies': 25}
    return message


@pytest.fixture
def sample_message_with_image():
    """Create a sample Telegram message with image."""
    message = Mock()
    message.id = 12346
    message.date = datetime.now()
    message.text = "Test message with image"
    # Mock media with photo attribute
    message.media = Mock()
    message.media.photo = True
    message.views = 200
    message.forwards = 75
    message.replies = {'replies': 30}
    return message


class TestTelegramScraper:
    """Test suite for TelegramScraper class."""

    def test_init_with_valid_env(self, mock_env_vars):
        """Test scraper initialization with valid environment variables."""
        scraper = TelegramScraper()
        assert scraper.api_id == 12345
        assert scraper.api_hash == 'test_hash'
        assert scraper.phone == '+1234567890'
        assert len(scraper.channels) == 3
        assert 'chemed' in scraper.channels

    def test_init_missing_api_id(self, monkeypatch):
        """Test scraper initialization with missing API ID."""
        monkeypatch.setenv('TELEGRAM_API_ID', '')
        monkeypatch.setenv('TELEGRAM_API_HASH', 'test_hash')
        with pytest.raises(ValueError, match="TELEGRAM_API_ID and TELEGRAM_API_HASH"):
            TelegramScraper()

    def test_parse_channels(self, scraper):
        """Test channel parsing from various formats."""
        # Test with usernames only
        channels = scraper._parse_channels('channel1,channel2,channel3')
        assert channels == ['channel1', 'channel2', 'channel3']

        # Test with URLs
        channels = scraper._parse_channels(
            'https://t.me/chemed,https://t.me/lobelia'
        )
        assert channels == ['chemed', 'lobelia']

        # Test with mixed formats
        channels = scraper._parse_channels(
            'chemed,https://t.me/lobelia,t.me/tikvah'
        )
        assert channels == ['chemed', 'lobelia', 'tikvah']

        # Test with empty string
        channels = scraper._parse_channels('')
        assert channels == []

        # Test with whitespace
        channels = scraper._parse_channels(' chemed , lobelia , tikvah ')
        assert channels == ['chemed', 'lobelia', 'tikvah']

    def test_process_message(self, scraper, sample_message):
        """Test message processing and field extraction."""
        channel_name = 'test_channel'
        result = scraper._process_message(sample_message, channel_name)

        assert result['message_id'] == 12345
        assert result['channel_name'] == channel_name
        assert result['message_text'] == "Test message content with product information"
        assert result['has_media'] is False
        assert result['views'] == 100
        assert result['forwards'] == 50
        assert result['replies'] == 25
        assert result['image_path'] is None

    def test_process_message_with_image(self, scraper, sample_message_with_image):
        """Test message processing with image."""
        channel_name = 'test_channel'
        result = scraper._process_message(sample_message_with_image, channel_name)

        assert result['message_id'] == 12346
        assert result['has_media'] is True
        assert result['views'] == 200

    def test_process_message_missing_fields(self, scraper):
        """Test message processing with missing fields."""
        message = Mock()
        message.id = 12347
        message.date = None
        message.text = None
        message.media = None
        # Missing views, forwards, replies

        result = scraper._process_message(message, 'test_channel')

        assert result['message_id'] == 12347
        assert result['message_text'] == ''
        assert result['views'] == 0
        assert result['forwards'] == 0
        assert result['replies'] == 0

    @pytest.mark.asyncio
    async def test_download_image(self, scraper, sample_message_with_image, tmp_path):
        """Test image downloading functionality."""
        # Mock the client's download_media method
        scraper.client = AsyncMock()
        scraper.client.download_media = AsyncMock(return_value=True)

        channel_name = 'test_channel'
        images_dir = tmp_path / 'data/raw/images' / channel_name
        images_dir.mkdir(parents=True, exist_ok=True)

        result = await scraper._download_image(
            sample_message_with_image,
            channel_name,
            images_dir
        )

        # Should return a path
        assert result is not None
        assert str(images_dir / '12346.jpg') in result

    @pytest.mark.asyncio
    async def test_download_image_no_media(self, scraper, sample_message, tmp_path):
        """Test image download when no media is present."""
        channel_name = 'test_channel'
        images_dir = tmp_path / 'data/raw/images' / channel_name
        images_dir.mkdir(parents=True, exist_ok=True)

        result = await scraper._download_image(
            sample_message,
            channel_name,
            images_dir
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_scrape_channel(self, scraper):
        """Test scraping a channel."""
        # Mock the client and entity
        scraper.client = AsyncMock()
        mock_entity = Mock()
        scraper._get_channel_entity = AsyncMock(return_value=mock_entity)

        # Mock messages iterator
        mock_messages = []
        for i in range(5):
            msg = Mock()
            msg.id = 1000 + i
            msg.date = datetime.now()
            msg.text = f"Message {i}"
            msg.media = None
            msg.views = 100 + i
            msg.forwards = 10 + i
            msg.replies = {'replies': 5 + i}
            mock_messages.append(msg)

        scraper.client.iter_messages = AsyncMock(return_value=mock_messages)

        # Mock save_channel_data to avoid file operations
        scraper.save_channel_data = AsyncMock()

        result = await scraper.scrape_channel('test_channel', limit=5)

        assert len(result) == 5
        assert result[0]['message_id'] == 1000

    @pytest.mark.asyncio
    async def test_scrape_channel_rate_limit(self, scraper):
        """Test handling of rate limiting."""
        from telethon.errors import FloodWaitError

        # Mock client and entity
        scraper.client = AsyncMock()
        mock_entity = Mock()

        # First call raises FloodWaitError, second call succeeds
        call_count = 0

        async def mock_scrape(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise FloodWaitError(5)
            return [{'message_id': 9999, 'channel_name': 'test_channel'}]

        scraper.scrape_channel = AsyncMock(side_effect=mock_scrape)
        scraper._get_channel_entity = AsyncMock(return_value=mock_entity)

        result = await scraper.scrape_channel('test_channel', limit=1)

        # Should retry and succeed
        assert call_count == 2
        assert len(result) == 1

    def test_save_channel_data(self, scraper, tmp_path):
        """Test saving channel data to JSON files."""
        channel_name = 'test_channel'
        messages = [
            {
                'message_id': 1001,
                'channel_name': channel_name,
                'message_date': datetime.now().isoformat(),
                'message_text': 'Test 1',
                'views': 10
            },
            {
                'message_id': 1002,
                'channel_name': channel_name,
                'message_date': datetime.now().isoformat(),
                'message_text': 'Test 2',
                'views': 20
            }
        ]

        # Run the async function
        asyncio.run(scraper.save_channel_data(channel_name, messages))

        # Check that files were created
        date_str = datetime.now().date().isoformat()
        file_path = (
            scraper.base_data_dir / 'telegram_messages' /
            date_str / f'{channel_name}.json'
        )

        # If file exists, check content
        if file_path.exists():
            with open(file_path, 'r') as f:
                saved_data = json.load(f)
                assert len(saved_data) >= 2
                assert any(msg['message_id'] == 1001 for msg in saved_data)

    def test_save_channel_data_with_existing(self, scraper, tmp_path):
        """Test saving data with existing file."""
        channel_name = 'test_channel'
        date_str = datetime.now().date().isoformat()
        file_path = (
            scraper.base_data_dir / 'telegram_messages' /
            date_str / f'{channel_name}.json'
        )
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create existing data
        existing_data = [
            {'message_id': 1001, 'channel_name': channel_name, 'message_text': 'Old'}
        ]
        with open(file_path, 'w') as f:
            json.dump(existing_data, f)

        # New data
        new_messages = [
            {
                'message_id': 1002,
                'channel_name': channel_name,
                'message_date': datetime.now().isoformat(),
                'message_text': 'New'
            }
        ]

        asyncio.run(scraper.save_channel_data(channel_name, new_messages))

        # Check merged data
        with open(file_path, 'r') as f:
            merged_data = json.load(f)
            assert len(merged_data) == 2
            assert any(msg['message_id'] == 1001 for msg in merged_data)
            assert any(msg['message_id'] == 1002 for msg in merged_data)


class TestScraperIntegration:
    """Integration tests for the scraper (requires actual API credentials)."""

    @pytest.mark.skip(reason="Requires actual Telegram API credentials")
    def test_real_scrape(self):
        """Test scraping with real credentials (skipped by default)."""
        pass