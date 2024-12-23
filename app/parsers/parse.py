# parsers/parse.py

import json
import logging
from bs4 import BeautifulSoup
from app.utils.helpers import clean_html

logger = logging.getLogger('parser')


def parse_rasstoyaniya_net_response(html, orderno):
    """
    Парсит HTML-ответ сервиса Расстояния.нет и извлекает данные из таблицы.

    :param html: HTML-контент
    :param orderno: Номер заказа
    :return: JSON-строка с результатами или ошибкой
    """

    # Очистка HTML
    cleaned_html = clean_html(html)
    logger.info(
        f"Расстояния.нет. Полученный HTML для order number {
            orderno}: {cleaned_html}"
    )

    soup = BeautifulSoup(cleaned_html, 'lxml')

    # Извлечение заголовка накладной
    header = soup.find('h5', class_='find-header')
    if header:
        invoice = header.get_text(strip=True)
    else:
        logger.error(
            f"Не удалось найти заголовок накладной для заказа {orderno}.")
        return json.dumps({"error": "Invoice header not found"}, ensure_ascii=False)

    # Извлечение данных из таблицы
    table = soup.find('table', class_='detail-view', id='quick_find')
    if not table:
        logger.error(f"Таблица с деталями не найдена для заказа {orderno}.")
        return json.dumps({"error": "Detail table not found"}, ensure_ascii=False)

    data = {"invoice": invoice}

    rows = table.find_all('tr')
    for row in rows:
        header_cell = row.find('th')
        data_cell = row.find('td')
        if header_cell and data_cell:
            key = header_cell.get_text(strip=True).rstrip(':')
            value = data_cell.get_text(strip=True)
            data[key] = value

    logger.info(
        f"Расстояния.нет. Полученные данные для order number {orderno}: {data}"
    )

    return json.dumps(data, ensure_ascii=False)


def parse_sp_service_response(html, orderno, region_name):
    """
    Парсит HTML-ответ СП-Сервис и извлекает данные.

    :param html: HTML-контент
    :param orderno: Номер заказа
    :param region_name: Название региона для логирования
    :return: JSON-строка с результатами или ошибкой
    """

    # Очистка HTML
    cleaned_html = clean_html(html)
    logger.info(
        f"СП-Сервис {region_name}. Полученный HTML для order number {orderno}: {cleaned_html}"
    )
    soup = BeautifulSoup(cleaned_html, 'lxml')

    # Извлечение заголовка накладной (если есть)
    header = soup.find('h5', class_='find-header')
    if header:
        invoice = header.get_text(strip=True)
    else:
        invoice = None  # Возможно, заголовок отсутствует

    # Извлечение данных из таблицы
    table = soup.find('table', class_='detail-view', id='quick_find')
    if not table:
        logger.error(f"Таблица с деталями не найдена для заказа {orderno}.")
        return json.dumps({"error": "Detail table not found"}, ensure_ascii=False)

    data = {}
    if invoice:
        data["invoice"] = invoice

    rows = table.find_all('tr')
    for row in rows:
        header_cell = row.find('th')
        data_cell = row.find('td')
        if header_cell and data_cell:
            key = header_cell.get_text(strip=True).rstrip(':')
            value = data_cell.get_text(strip=True)
            data[key] = value

    logger.info(
        f"СП-Сервис {region_name}. Полученные данные для order number {orderno}: {data}"
    )

    return json.dumps(data, ensure_ascii=False)


def parse_sib_express_response(html, orderno):
    """
    Парсит HTML-ответ сервиса Сиб-Экспресс и извлекает данные из таблицы.

    :param html: HTML-контент
    :param orderno: Номер заказа
    :return: JSON-строка с результатами или ошибкой
    """

    # Очистка HTML
    cleaned_html = clean_html(html)
    logger.info(
        f"Сиб-Экспресс. Полученный HTML для order number {
            orderno}: {cleaned_html}"
    )

    soup = BeautifulSoup(cleaned_html, 'lxml')

    # Извлечение заголовка накладной
    header = soup.find('h5', class_='find-header')
    if header:
        invoice = header.get_text(strip=True)
    else:
        logger.error(
            f"Не удалось найти заголовок накладной для заказа {orderno}.")
        return json.dumps({"error": "Invoice header not found"}, ensure_ascii=False)

    # Извлечение данных из таблицы
    table = soup.find('table', class_='detail-view', id='quick_find')
    if not table:
        logger.error(f"Таблица с деталями не найдена для заказа {orderno}.")
        return json.dumps({"error": "Detail table not found"}, ensure_ascii=False)

    data = {"invoice": invoice}

    rows = table.find_all('tr')
    for row in rows:
        header_cell = row.find('th')
        data_cell = row.find('td')
        if header_cell and data_cell:
            key = header_cell.get_text(strip=True).rstrip(':')
            value = data_cell.get_text(strip=True)
            data[key] = value

    logger.info(
        f"Сиб-Экспресс. Полученные данные для order number {orderno}: {data}"
    )

    return json.dumps(data, ensure_ascii=False)