import os
from dataclasses import dataclass


@dataclass
class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')

    # Yandex Music URL
    YANDEX_MUSIC_URL: str = os.getenv('YANDEX_MUSIC_URL', 'https://music.yandex.ru/album/37711786')

    # Monitoring interval in seconds
    MONITOR_INTERVAL: int = int(os.getenv('MONITOR_INTERVAL', 3600))

    # Request headers to mimic real browser
    HEADERS: dict = None

    def __post_init__(self):
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }


config = Config()