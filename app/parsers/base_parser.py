# Базовый класс для всех парсеров
import logging

from bs4 import BeautifulSoup

logger = logging.getLogger("parser")


class BaseParser:
    name = "BaseParser"  # Название парсера
    url = "url"
    cookies = {}
    referer_suffix = "suffix"

    def _get_headers(self, custom_headers=None):
        """Возвращает базовые заголовки с возможностью добавления пользовательских."""
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8,it;q=0.7",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def get_html(self, orderno):
        raise NotImplementedError("Этот метод должен быть переопределён в подклассах.")

    def _get_table(self, html, class_name=None, table_id=None):
        """
        Ищет таблицу по указанным параметрам (класс и/или идентификатор).
        Если параметры не заданы, ищет первую таблицу.
        """
        soup = BeautifulSoup(html, "lxml")

        # Фильтры для поиска таблицы
        if class_name or table_id:
            search_params = {}
            if class_name:
                search_params["class_"] = lambda x: x and class_name in x
            if table_id:
                search_params["id"] = table_id

            # Поиск таблицы с фильтрами
            table = soup.find("table", **search_params)
        else:
            # Если не задано ни class_name, ни table_id, ищем первую таблицу
            table = soup.find("table")

        if not table:
            logger.error(f"""{self.name}. Таблица с классом '{class_name}' и ID '{table_id}' не найдена.""")
        return table

    def extract_table_data(self, table, key_tag="td", min_cells=2, exact_cells=None):
        """
        Универсальная функция для извлечения данных из таблицы.

        :param table: Объект таблицы (BeautifulSoup).
        :param key_tag: Тег для ключей (по умолчанию 'td').
        :param min_cells: Минимальное количество ячеек в строке.
        :param exact_cells: Точное количество ячеек в строке (если задано, игнорирует min_cells).
        :return: Словарь с извлечёнными данными.
        """
        data = {}
        rows = table.find_all("tr")  # Ищем все строки таблицы
        for row in rows:
            cells = row.find_all(key_tag)  # Находим ячейки по тегу
            if exact_cells and len(cells) != exact_cells:
                continue  # Пропускаем строки, где ячеек меньше/больше, чем требуется
            if len(cells) >= min_cells:
                key = cells[0].get_text(strip=True)  # Первый элемент — ключ
                value = cells[1].get_text(strip=True) if len(cells) > 1 else None  # Второй элемент — значение
                if key and value:
                    # Убираем двоеточие в конце ключа, если оно есть
                    data[key.rstrip(":")] = value
        return data

    def parse(self, orderno):
        raise NotImplementedError("Этот метод должен быть переопределён в подклассах.")

    def process_delivered_info(self, info):
        raise NotImplementedError("Этот метод должен быть переопределён в подклассах.")
