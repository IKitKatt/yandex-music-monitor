import time
import requests
import logging
from config import config


class TelegramBot:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.logger = logging.getLogger(__name__)
        self._poll_offset = 0

    def send_message(self, text: str, chat_id: str = None) -> bool:
        """
        Отправляет сообщение в Telegram чат
        """
        target_chat = chat_id or self.chat_id
        if not self.token or not target_chat:
            self.logger.error("Telegram bot token или chat ID не настроены")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': target_chat,
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

        interval_minutes = config.MONITOR_INTERVAL // 60
        interval_seconds = config.MONITOR_INTERVAL % 60

        if interval_minutes > 0:
            interval_text = f"{interval_minutes} мин {interval_seconds} сек"
        else:
            interval_text = f"{interval_seconds} сек"

        message += f"\n⏰ <i>Следующее обновление через: {interval_text}</i>"

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

    def _format_period_stats(self, was: int, became: int, days: int) -> str:
        change = became - was
        if change > 0:
            change_str = f"+{change:,}"
        elif change < 0:
            change_str = f"{change:,}"
        else:
            change_str = "без изменений"

        period_label = f"последние {days} дней"
        if days == 7:
            period_label = "последние 7 дней (неделя)"
        elif days == 30:
            period_label = "последние 30 дней (месяц)"

        message = f"📊 <b>Статистика за {period_label}</b>\n\n"
        message += f"Было:       {was:,}\n"
        message += f"Стало:      {became:,}\n"
        message += f"Изменение: {change_str}"
        return message

    def start_polling(self, db):
        """
        Запускает long polling для обработки команд /week и /month.
        Предназначен для запуска в отдельном потоке.
        """
        self.logger.info("Запуск polling для обработки команд...")
        while True:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._handle_update(update, db)
            except Exception as e:
                self.logger.error(f"Ошибка polling: {e}")
                time.sleep(5)

    def _get_updates(self) -> list:
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                'offset': self._poll_offset,
                'timeout': 30,
                'allowed_updates': ['message']
            }
            response = requests.get(url, params=params, timeout=40)
            response.raise_for_status()
            data = response.json()
            return data.get('result', [])
        except requests.RequestException as e:
            self.logger.error(f"Ошибка getUpdates: {e}")
            return []

    def _handle_update(self, update: dict, db):
        self._poll_offset = update['update_id'] + 1

        message = update.get('message', {})
        text = message.get('text', '').strip()
        chat_id = str(message.get('chat', {}).get('id', ''))

        if not text or not chat_id:
            return

        command = text.split('@')[0]

        if command == '/week':
            was, became = db.get_stats(7)
            if was is None:
                self.send_message("Нет данных за последние 7 дней.", chat_id)
            else:
                self.send_message(self._format_period_stats(was, became, 7), chat_id)

        elif command == '/month':
            was, became = db.get_stats(30)
            if was is None:
                self.send_message("Нет данных за последние 30 дней.", chat_id)
            else:
                self.send_message(self._format_period_stats(was, became, 30), chat_id)
