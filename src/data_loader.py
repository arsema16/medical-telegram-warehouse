"""
Data Loader
Loads scraped JSON data into PostgreSQL database.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class DataLoader:
    """
    Loads scraped Telegram data from JSON files into PostgreSQL.
    """

    def __init__(self):
        """Initialize database connection."""
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'medical_warehouse'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        self.connection = None
        self.data_dir = Path('data/raw/telegram_messages')

    def connect(self) -> None:
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(**self.conn_params)
            self.connection.autocommit = False
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def create_raw_table(self) -> None:
        """Create raw.telegram_messages table if it doesn't exist."""
        create_table_sql = """
        CREATE SCHEMA IF NOT EXISTS raw;

        CREATE TABLE IF NOT EXISTS raw.telegram_messages (
            message_id BIGINT PRIMARY KEY,
            channel_name VARCHAR(100) NOT NULL,
            message_date TIMESTAMP,
            message_text TEXT,
            has_media BOOLEAN DEFAULT FALSE,
            image_path TEXT,
            views INTEGER DEFAULT 0,
            forwards INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_data JSONB
        );

        CREATE INDEX IF NOT EXISTS idx_raw_channel_date
        ON raw.telegram_messages (channel_name, message_date);

        CREATE INDEX IF NOT EXISTS idx_raw_has_media
        ON raw.telegram_messages (has_media);
        """

        try:
            with self.connection.cursor() as cur:
                cur.execute(create_table_sql)
            self.connection.commit()
            logger.info("Raw table created successfully")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to create raw table: {e}")
            raise

    def load_json_files(self, date_filter: Optional[str] = None) -> List[Dict]:
        """
        Load messages from JSON files.

        Args:
            date_filter: Specific date to load (YYYY-MM-DD), or None for all

        Returns:
            List of message dictionaries
        """
        messages = []

        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return messages

        # Get date directories
        date_dirs = []
        if date_filter:
            date_path = self.data_dir / date_filter
            if date_path.exists():
                date_dirs = [date_path]
        else:
            date_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]

        for date_dir in date_dirs:
            for json_file in date_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        file_msgs = json.load(f)
                        messages.extend(file_msgs)
                        logger.debug(
                            f"Loaded {len(file_msgs)} messages from {json_file}"
                        )
                except Exception as e:
                    logger.error(f"Failed to load {json_file}: {e}")

        logger.info(f"Loaded {len(messages)} total messages from JSON files")
        return messages

    def load_to_database(self, messages: List[Dict], batch_size: int = 1000) -> int:
        """
        Load messages to PostgreSQL database.

        Args:
            messages: List of message dictionaries
            batch_size: Number of records per batch

        Returns:
            Number of records loaded
        """
        if not messages:
            logger.warning("No messages to load")
            return 0

        loaded_count = 0

        # SQL for inserting/upserting data
        insert_sql = """
        INSERT INTO raw.telegram_messages (
            message_id, channel_name, message_date, message_text,
            has_media, image_path, views, forwards, replies, raw_data
        ) VALUES %s
        ON CONFLICT (message_id) DO UPDATE SET
            channel_name = EXCLUDED.channel_name,
            message_date = EXCLUDED.message_date,
            message_text = EXCLUDED.message_text,
            has_media = EXCLUDED.has_media,
            image_path = EXCLUDED.image_path,
            views = EXCLUDED.views,
            forwards = EXCLUDED.forwards,
            replies = EXCLUDED.replies,
            raw_data = EXCLUDED.raw_data
        """

        try:
            with self.connection.cursor() as cur:
                # Process in batches
                for i in range(0, len(messages), batch_size):
                    batch = messages[i:i + batch_size]

                    # Prepare data for batch insert
                    batch_data = []
                    for msg in batch:
                        raw_json = json.dumps(msg)
                        message_date = None
                        if msg.get('message_date'):
                            try:
                                message_date = datetime.fromisoformat(
                                    msg['message_date']
                                )
                            except (ValueError, TypeError):
                                pass

                        batch_data.append((
                            msg.get('message_id'),
                            msg.get('channel_name'),
                            message_date,
                            msg.get('message_text', ''),
                            msg.get('has_media', False),
                            msg.get('image_path'),
                            msg.get('views', 0),
                            msg.get('forwards', 0),
                            msg.get('replies', 0),
                            raw_json
                        ))

                    # Execute batch insert
                    execute_values(cur, insert_sql, batch_data)
                    self.connection.commit()

                    loaded_count += len(batch)
                    logger.info(
                        f"Loaded batch {i//batch_size + 1}: {len(batch)} records"
                    )

            logger.info(f"Successfully loaded {loaded_count} messages to database")

        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to load data: {e}")
            raise

        return loaded_count

    def load_all(self, date_filter: Optional[str] = None) -> int:
        """
        Load all messages from JSON files to database.

        Args:
            date_filter: Specific date to load

        Returns:
            Number of records loaded
        """
        try:
            self.connect()
            self.create_raw_table()

            messages = self.load_json_files(date_filter)
            loaded = self.load_to_database(messages)

            return loaded

        except Exception as e:
            logger.error(f"Load process failed: {e}")
            raise
        finally:
            self.close()


def main():
    """Main entry point for data loader."""
    loader = DataLoader()

    # Optional: specify a date filter
    # loader.load_all(date_filter='2026-06-25')
    loader.load_all()


if __name__ == "__main__":
    main()