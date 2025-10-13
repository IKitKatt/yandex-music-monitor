import requests
import re
import logging
import json
from bs4 import BeautifulSoup
from config import config


class YandexMusicParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)
        self.logger = logging.getLogger(__name__)

    def get_subscribers_count(self) -> int:
        """
        Получает количество подписчиков из likesCount в исходном коде страницы
        """
        try:
            response = self.session.get(config.YANDEX_MUSIC_URL, timeout=10)
            response.raise_for_status()

            # Ищем likesCount в исходном коде страницы
            subscribers = self._parse_likes_count(response.text)

            if subscribers is not None:
                self.logger.info(f"Найдено подписчиков: {subscribers}")
                return subscribers
            else:
                self.logger.warning("Не удалось найти likesCount на странице")
                return 0

        except requests.RequestException as e:
            self.logger.error(f"Ошибка при запросе: {e}")
            return 0
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка: {e}")
            return 0

    def _parse_likes_count(self, html: str) -> int:
        """
        Парсит likesCount из исходного кода страницы
        """
        try:
            # Метод 1: Поиск в JSON данных
            subscribers = self._parse_from_store_data(html)
            if subscribers is not None:
                return subscribers

            # Метод 2: Поиск через регулярные выражения
            subscribers = self._parse_with_regex(html)
            if subscribers is not None:
                return subscribers

            # Метод 3: Поиск в script тегах
            subscribers = self._parse_from_scripts(html)
            if subscribers is not None:
                return subscribers

        except Exception as e:
            self.logger.debug(f"Ошибка при парсинге likesCount: {e}")

        return None

    def _parse_from_store_data(self, html: str) -> int:
        """
        Парсит данные из store данных в JavaScript
        """
        try:
            # Ищем store данные
            store_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'var\s+store\s*=\s*({.*?});',
                r'window\.store\s*=\s*({.*?});'
            ]

            for pattern in store_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    store_data = match.group(1)
                    data = json.loads(store_data)

                    # Рекурсивный поиск likesCount в JSON
                    subscribers = self._find_likes_count(data)
                    if subscribers is not None:
                        return subscribers

        except Exception as e:
            self.logger.debug(f"Ошибка при парсинге store данных: {e}")

        return None

    def _find_likes_count(self, data):
        """
        Рекурсивно ищет likesCount в JSON структуре
        """
        if isinstance(data, dict):
            # Проверяем текущий уровень
            if 'likesCount' in data:
                return data['likesCount']

            # Рекурсивно проверяем все значения
            for key, value in data.items():
                result = self._find_likes_count(value)
                if result is not None:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = self._find_likes_count(item)
                if result is not None:
                    return result

        return None

    def _parse_with_regex(self, html: str) -> int:
        """
        Парсит likesCount с помощью регулярных выражений
        """
        try:
            # Прямой поиск likesCount в коде
            patterns = [
                r'"likesCount"\s*:\s*(\d+)',
                r"'likesCount'\s*:\s*(\d+)",
                r'likesCount["\']?\s*:\s*["\']?(\d+)',
                r'likesCount\s*=\s*(\d+)'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if match.isdigit():
                        return int(match)

        except Exception as e:
            self.logger.debug(f"Ошибка при regex парсинге: {e}")

        return None

    def _parse_from_scripts(self, html: str) -> int:
        """
        Парсит данные из script тегов
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            scripts = soup.find_all('script')

            for script in scripts:
                if script.string:
                    script_content = script.string

                    # Ищем в содержимом script тегов
                    subscribers = self._parse_with_regex(script_content)
                    if subscribers is not None:
                        return subscribers

                    # Ищем store данные в script тегах
                    subscribers = self._parse_from_store_data(script_content)
                    if subscribers is not None:
                        return subscribers

        except Exception as e:
            self.logger.debug(f"Ошибка при парсинге script тегов: {e}")

        return None

    def debug_page_content(self):
        """
        Метод для отладки - сохраняет HTML страницы для анализа
        """
        try:
            response = self.session.get(config.YANDEX_MUSIC_URL, timeout=10)
            response.raise_for_status()

            # Сохраняем HTML для анализа
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)

            self.logger.info("Страница сохранена в debug_page.html для анализа")

            # Ищем все упоминания likesCount
            likes_matches = re.findall(r'likesCount["\']?\s*:\s*["\']?(\d+)', response.text)
            self.logger.info(f"Найдены matches likesCount: {likes_matches}")

        except Exception as e:
            self.logger.error(f"Ошибка при отладке: {e}")