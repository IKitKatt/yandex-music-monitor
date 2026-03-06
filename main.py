import time
import logging
import signal
import sys
import threading
from datetime import datetime
from parser import YandexMusicParser
from bot import TelegramBot
from config import config
from database import Database


class Monitor:
    def __init__(self):
        self.parser = YandexMusicParser()
        self.bot = TelegramBot()
        self.db = Database()
        self.last_count = None
        self.is_running = True
        self.setup_logging()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/monitor.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def signal_handler(self, signum, frame):
        self.logger.info("Получен сигнал остановки...")
        self.is_running = False

    def debug_first_run(self):
        """
        Запускает отладку при первом запуске для проверки парсинга
        """
        self.logger.info("Запуск отладки парсера...")
        self.parser.debug_page_content()

    def run(self):
        """
        Основной цикл мониторинга
        """
        self.logger.info("Запуск мониторинга Яндекс.Музыки...")

        self.debug_first_run()

        # Запуск polling в отдельном потоке
        polling_thread = threading.Thread(
            target=self.bot.start_polling,
            args=(self.db,),
            daemon=True,
            name="BotPolling"
        )
        polling_thread.start()

        interval_seconds = config.MONITOR_INTERVAL
        hours = interval_seconds // 3600
        minutes = (interval_seconds % 3600) // 60
        seconds = interval_seconds % 60
        parts = []
        if hours > 0:
            parts.append(f"{hours} ч")
        if minutes > 0:
            parts.append(f"{minutes} мин")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} сек")
        interval_text = " ".join(parts)

        startup_message = "🚀 <b>Мониторинг Яндекс.Музыки запущен!</b>\n\n"
        startup_message += f"📊 Отслеживается страница: {config.YANDEX_MUSIC_URL}\n"
        startup_message += f"⏰ Интервал публикации: {interval_text}"
        self.bot.send_message(startup_message)

        iteration = 0
        while self.is_running:
            try:
                iteration += 1
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.logger.info(f"Итерация #{iteration} - Проверка количества подписчиков...")

                current_count = self.parser.get_subscribers_count()

                if current_count > 0:
                    self.db.save_count(current_count)

                    if current_count != self.last_count:
                        message = self.bot.format_subscribers_message(
                            current_count,
                            self.last_count,
                            current_time,
                            iteration
                        )

                        if self.bot.send_message(message):
                            self.last_count = current_count
                            self.logger.info(f"Сообщение #{iteration} успешно отправлено")
                        else:
                            self.logger.error(f"Не удалось отправить сообщение #{iteration}")
                    else:
                        self.logger.info(f"Итерация #{iteration}: изменений нет, сообщение не отправлено")
                else:
                    self.logger.warning("Не удалось получить количество подписчиков")
                    error_message = self.bot.format_error_message(current_time, iteration)
                    self.bot.send_message(error_message)

                self.logger.info(f"Итерация #{iteration} завершена. Подписчиков: {current_count}")

            except Exception as e:
                self.logger.error(f"Ошибка в основном цикле на итерации #{iteration}: {e}")
                error_message = self.bot.format_error_message(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    iteration,
                    str(e)
                )
                self.bot.send_message(error_message)

            if self.is_running:
                self.logger.info(f"Ожидание {config.MONITOR_INTERVAL} секунд до следующей публикации...")
                for i in range(config.MONITOR_INTERVAL):
                    if not self.is_running:
                        break
                    if i % 60 == 0:
                        self.logger.debug(f"Осталось {config.MONITOR_INTERVAL - i} секунд...")
                    time.sleep(1)

        shutdown_message = "🛑 <b>Мониторинг Яндекс.Музыки остановлен</b>"
        self.bot.send_message(shutdown_message)
        self.logger.info("Мониторинг остановлен")


if __name__ == "__main__":
    monitor = Monitor()
    monitor.run()
