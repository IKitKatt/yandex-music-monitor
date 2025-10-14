import requests
import logging
from config import config


class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.logger = logging.getLogger(__name__)

    def send_message(self, text: str) -> bool:
        """
        Отправляет сообщение в Telegram чат
        """
        if not self.token or not self.chat_id:
            self.logger.error("Telegram bot token или chat ID не настроены")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            self.logger.info("Сообщение успешно отправлено в Telegram")
            return True

        except requests.RequestException as e:
            self.logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            return False

    def format_subscribers_message(self, count: int, previous_count: int = None,
                                   timestamp: str = None, iteration: int = None) -> str:
        """
        Форматирует сообщение о количестве подписчиков
        """
        message = f"🎵 <b>Статистика Яндекс.Музыки</b>\n\n"
        message += f"👥 <b>Текущее количество подписчиков:</b> {count:,}\n"

        if previous_count is not None:
            difference = count - previous_count
            if difference > 0:
                message += f"📈 <b>Изменение:</b> +{difference}\n"
            elif difference < 0:
                message += f"📉 <b>Изменение:</b> {difference}\n"
            else:
                message += f"➡️ <b>Изменение:</b> без изменений\n"

        if timestamp:
            message += f"🕒 <b>Время проверки:</b> {timestamp}\n"

        # Добавляем информацию об интервале
        interval_minutes = config.MONITOR_INTERVAL // 60
        interval_seconds = config.MONITOR_INTERVAL % 60

        if interval_minutes > 0:
            interval_text = f"{interval_minutes} мин {interval_seconds} сек"
        else:
            interval_text = f"{interval_seconds} сек"

        message += f"\n⏰ <i>Следующее обновление через: {interval_text}</i>\n"
        message += f"🔍 <i>Данные получены из likesCount</i>"

        return message

    def format_error_message(self, timestamp: str = None, iteration: int = None, error: str = None) -> str:
        """
        Форматирует сообщение об ошибке
        """
        message = "❌ <b>Ошибка получения данных</b>\n\n"
        message += "Не удалось получить количество подписчиков.\n"

        if error:
            message += f"<b>Ошибка:</b> {error}\n"

        if timestamp:
            message += f"🕒 <b>Время проверки:</b> {timestamp}\n"

        message += "\n⚠️ <i>Проверьте доступность страницы Яндекс.Музыки</i>"

        return message