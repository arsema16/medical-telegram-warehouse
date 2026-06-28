"""
Telegram Data Scraper
Extracts messages, images, and metadata from public Telegram channels.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import re

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramScraper:
    """
    Scraper for extracting data from public Telegram channels.
    """

    def __init__(self):
        """Initialize scraper with Telegram API credentials."""
        self.api_id = int(os.getenv('TELEGRAM_API_ID', 0))
        self.api_hash = os.getenv('TELEGRAM_API_HASH', '')
        self.phone = os.getenv('TELEGRAM_PHONE', '')
        self.channels = self._parse_channels(
            os.getenv('TELEGRAM_CHANNELS', '')
        )

        if not self.api_id or not self.api_hash:
            raise ValueError(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env"
            )

        self.client = TelegramClient('session', self.api_id, self.api_hash)
        self.base_data_dir = Path('data/raw')
        self.base_data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Scraper initialized with {len(self.channels)} channels")

    def _parse_channels(self, channels_str: str) -> List[str]:
        """
        Parse channel names from environment variable.

        Args:
            channels_str: Comma-separated channel names or URLs

        Returns:
            List of channel usernames
        """
        if not channels_str:
            return []

        channels = []
        for item in channels_str.split(','):
            item = item.strip()
            if not item:
                continue

            # Extract username from URL if present
            if 't.me/' in item:
                # Handle https://t.me/username or t.me/username
                match = re.search(r't\.me/([^/]+)', item)
                if match:
                    channels.append(match.group(1))
            else:
                channels.append(item)

        return channels

    async def _get_channel_entity(self, channel_name: str):
        """
        Get channel entity from username.

        Args:
            channel_name: Channel username

        Returns:
            Channel entity object
        """
        try:
            if channel_name.startswith('@'):
                channel_name = channel_name[1:]
            return await self.client.get_entity(f'@{channel_name}')
        except Exception as e:
            logger.error(f"Failed to get entity for {channel_name}: {e}")
            return None

    async def scrape_channel(
        self,
        channel_name: str,
        limit: int = 1000,
        start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape messages from a specific channel.

        Args:
            channel_name: Channel username
            limit: Maximum number of messages to scrape
            start_date: Only scrape messages after this date

        Returns:
            List of message dictionaries
        """
        messages_data = []
        images_dir = self.base_data_dir / 'images' / channel_name
        images_dir.mkdir(parents=True, exist_ok=True)

        entity = await self._get_channel_entity(channel_name)
        if not entity:
            logger.error(f"Skipping {channel_name} - entity not found")
            return messages_data

        try:
            logger.info(f"Scraping {channel_name}...")

            # Collect messages
            message_count = 0
            async for message in self.client.iter_messages(
                entity,
                limit=limit,
                offset_date=start_date
            ):
                if not message:
                    continue

                # Process message
                msg_data = self._process_message(message, channel_name)

                # Download image if present
                if message.media and hasattr(message.media, 'photo'):
                    image_path = await self._download_image(
                        message,
                        channel_name,
                        images_dir
                    )
                    if image_path:
                        msg_data['image_path'] = str(image_path)
                        msg_data['has_media'] = True

                messages_data.append(msg_data)
                message_count += 1

                if message_count % 100 == 0:
                    logger.info(
                        f"Scraped {message_count} messages from {channel_name}"
                    )

            logger.info(
                f"Completed {channel_name}: {len(messages_data)} messages scraped"
            )

        except FloodWaitError as e:
            logger.warning(
                f"Rate limited on {channel_name}, waiting {e.seconds} seconds"
            )
            await asyncio.sleep(e.seconds)
            # Recursive call after waiting
            return await self.scrape_channel(channel_name, limit, start_date)
        except Exception as e:
            logger.error(f"Error scraping {channel_name}: {e}")

        return messages_data

    def _process_message(self, message, channel_name: str) -> Dict[str, Any]:
        """
        Process a single message and extract relevant fields.

        Args:
            message: Telegram message object
            channel_name: Channel name

        Returns:
            Dictionary of message data
        """
        msg_data = {
            'message_id': message.id,
            'channel_name': channel_name,
            'message_date': message.date.isoformat() if message.date else None,
            'message_text': message.text or '',
            'has_media': bool(message.media),
            'image_path': None,
            'views': getattr(message, 'views', 0),
            'forwards': getattr(message, 'forwards', 0),
            'replies': getattr(message, 'replies', {}).get('replies', 0)
            if hasattr(message, 'replies') else 0
        }
        return msg_data


    async def _download_image(
        self,
        message,
        channel_name: str,
        images_dir: Path
    ) -> Optional[str]:
        """
        Download image from message.

        Args:
            message: Telegram message object
            channel_name: Channel name
            images_dir: Directory to save images

        Returns:
            Path to downloaded image or None
        """
        try:
            if not message.media:
                return None

            # Create filename based on message_id
            filename = f"{message.id}.jpg"
            filepath = images_dir / filename

            # Check if image already exists
            if filepath.exists():
                return str(filepath)

            # Download image
            await self.client.download_media(
                message.media,
                file=str(filepath)
            )

            logger.debug(f"Downloaded image: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to download image for message {message.id}: {e}")
            return None

    async def scrape_all_channels(self, limit: int = 1000) -> Dict[str, List[Dict]]:
        """
        Scrape all configured channels.

        Args:
            limit: Maximum messages per channel

        Returns:
            Dictionary mapping channel names to message data
        """
        all_messages = {}

        for channel in self.channels:
            try:
                messages = await self.scrape_channel(channel, limit=limit)
                if messages:
                    all_messages[channel] = messages
                    await self.save_channel_data(channel, messages)
            except Exception as e:
                logger.error(f"Failed to scrape {channel}: {e}")

        return all_messages

    async def save_channel_data(self, channel_name: str, messages: List[Dict]) -> None:
        """
        Save scraped data to JSON files organized by date.

        Args:
            channel_name: Channel name
            messages: List of message dictionaries
        """
        if not messages:
            logger.warning(f"No messages to save for {channel_name}")
            return

        # Group messages by date
        messages_by_date = {}
        for msg in messages:
            try:
                date = datetime.fromisoformat(msg['message_date']).date()
                date_str = date.isoformat()
                if date_str not in messages_by_date:
                    messages_by_date[date_str] = []
                messages_by_date[date_str].append(msg)
            except Exception as e:
                logger.warning(
                    f"Could not parse date for message "
                    f"{msg.get('message_id')}: {e}"
                )
                # Put in 'unknown' date folder
                if 'unknown' not in messages_by_date:
                    messages_by_date['unknown'] = []
                messages_by_date['unknown'].append(msg)

        # Save each date's data
        for date_str, msgs in messages_by_date.items():
            date_dir = self.base_data_dir / 'telegram_messages' / date_str
            date_dir.mkdir(parents=True, exist_ok=True)

            file_path = date_dir / f"{channel_name}.json"

            # Load existing data if file exists
            existing_msgs = []
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_msgs = json.load(f)

            # Merge and deduplicate by message_id
            all_msgs = existing_msgs + msgs
            seen_ids = set()
            unique_msgs = []
            for msg in all_msgs:
                msg_id = msg.get('message_id')
                if msg_id and msg_id not in seen_ids:
                    seen_ids.add(msg_id)
                    unique_msgs.append(msg)

            # Save merged data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(unique_msgs, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Saved {len(unique_msgs)} messages for {channel_name} "
                f"on {date_str}"
            )

    def run(self, limit: int = 1000) -> None:
        """
        Run the scraper synchronously.

        Args:
            limit: Maximum messages per channel
        """
        with self.client:
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(self.scrape_all_channels(limit=limit))
            except KeyboardInterrupt:
                logger.info("Scraping interrupted by user")
            finally:
                loop.close()


def main():
    """Main entry point for scraper."""
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)

    # Initialize scraper
    scraper = TelegramScraper()

    # Run scraper
    scraper.run(limit=2000)


if __name__ == "__main__":
    main()