import time
import logging
import signal
import sys
from datetime import datetime
from parser import YandexMusicParser
from bot import TelegramBot
from config import config


class Monitor:
    def __init__(self):
        self.parser = YandexMusicParser()
        self.bot = TelegramBot()
        self.last_count = None
        self.is_running = True
        self.setup_logging()

        # Обработка сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('monitor.log')
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

        # Запускаем отладку при первом запуске
        self.debug_first_run()

        # Первоначальная отправка сообщения о запуске
        startup_message = "🚀 <b>Мониторинг Яндекс.Музыки запущен!</b>\n\n"
        startup_message += f"📊 Отслеживается страница: {config.YANDEX_MUSIC_URL}\n"
        startup_message += f"⏰ Интервал проверки: {config.MONITOR_INTERVAL // 3600} час(а/ов)\n"
        startup_message += f"🔍 Метод парсинга: поиск likesCount в исходном коде"
        self.bot.send_message(startup_message)

        while self.is_running:
            try:
                self.logger.info("Проверка количества подписчиков...")

                # Получаем текущее количество подписчиков
                current_count = self.parser.get_subscribers_count()

                if current_count > 0:
                    # Формируем и отправляем сообщение
                    message = self.bot.format_subscribers_message(
                        current_count,
                        self.last_count
                    )

                    # Отправляем сообщение только если количество изменилось или это первая проверка
                    if self.last_count is None or current_count != self.last_count:
                        if self.bot.send_message(message):
                            self.last_count = current_count
                    else:
                        self.logger.info("Количество подписчиков не изменилось")
                else:
                    self.logger.warning("Не удалось получить количество подписчиков")
                    # Отправляем сообщение об ошибке только если до этого были успешные запросы
                    if self.last_count is not None:
                        error_message = "❌ <b>Ошибка получения данных</b>\n\nНе удалось получить количество подписчиков. Проверьте доступность страницы."
                        self.bot.send_message(error_message)

                # Логируем текущее состояние
                self.logger.info(f"Текущее количество подписчиков: {current_count}")

            except Exception as e:
                self.logger.error(f"Ошибка в основном цикле: {e}")
                # Отправляем сообщение об ошибке
                error_message = f"❌ <b>Ошибка в работе монитора</b>\n\n{str(e)}"
                self.bot.send_message(error_message)

            # Ожидание до следующей проверки
            if self.is_running:
                self.logger.info(f"Ожидание {config.MONITOR_INTERVAL} секунд до следующей проверки...")
                for _ in range(config.MONITOR_INTERVAL):
                    if not self.is_running:
                        break
                    time.sleep(1)

        # Отправляем сообщение об остановке
        shutdown_message = "🛑 <b>Мониторинг Яндекс.Музыки остановлен</b>"
        self.bot.send_message(shutdown_message)
        self.logger.info("Мониторинг остановлен")


if __name__ == "__main__":
    monitor = Monitor()
    monitor.run()