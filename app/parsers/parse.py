# parsers/parse.py
import json
import logging
from bs4 import BeautifulSoup
from app.utils.helpers import clean_html

logger = logging.getLogger('parser')


def parse_rasstoyaniya_net_response(html, orderno):
    cleaned_html = clean_html(html)
    logger.info(
        f"Расстояния.нет. Полученный HTML для order number {orderno}: {cleaned_html}")
    try:
        soup = BeautifulSoup(cleaned_html, 'lxml')

        # Извлечение заголовка накладной
        header = soup.find('h5', class_='find-header')
        if header:
            invoice = header.get_text(strip=True)
        else:
            logger.error(
                f"Расстояния.нет. Не удалось найти заголовок накладной для заказа {orderno}.")
            return json.dumps({"error": "Invoice header not found"}, ensure_ascii=False)

        # Извлечение данных из таблицы
        table = soup.find('table', class_='detail-view', id='quick_find')
        if not table:
            logger.error(
                f"Таблица с деталями не найдена для заказа {orderno}.")
            return {"error": "Detail table not found"}

        data = {"invoice": invoice}

        rows = table.find_all('tr')
        for row in rows:
            header_cell = row.find('th')
            data_cell = row.find('td')
            if header_cell and data_cell:
                key = header_cell.get_text(strip=True).rstrip(':')
                value = data_cell.get_text(strip=True)
                data[key] = value

        logger.info(f"""Расстояния.нет. Полученные данные для заказа {
                    orderno}: {data}""")
        return data
    except Exception as e:
        logger.error(f"Ошибка при обработке заказа {orderno}: {e}")
        return {"error": str(e)}


def parse_sp_service_response(html, orderno, region_name):
    try:
        cleaned_html = clean_html(html)
        logger.info(
            f"СП-Сервис {region_name}. Полученный HTML для order number {orderno}: {cleaned_html}")
        soup = BeautifulSoup(cleaned_html, 'lxml')
        all_tables = soup.find_all('table')
        logger.debug(f"""Найденные таблицы: {
                     [str(table)[:200] for table in all_tables]}""")

        # Попробуем найти таблицу с данными
        table = soup.find('table', class_=lambda x: x and 'table-striped' in x)

        if not table:
            logger.error(
                f"Таблица с деталями не найдена для заказа {orderno}.")
            return json.dumps({"error": "Detail table not found"}, ensure_ascii=False)

        data = {}
        rows = table.find_all('tr')
        for row in rows:
            header_cell = row.find('td')  # Используем <td> для первой ячейки
            data_cell = row.find_all('td')[1] if len(
                row.find_all('td')) > 1 else None
            if header_cell and data_cell:
                key = header_cell.get_text(strip=True).rstrip(':')
                value = data_cell.get_text(strip=True)
                data[key] = value

        logger.info(
            f"СП-Сервис {region_name}. Полученные данные для order number {orderno}: {data}")
        return data

    except Exception as e:
        logger.error(f"Ошибка при обработке заказа {orderno}: {e}")
        return {"error": str(e)}


def parse_sib_express_response(html, orderno):
    try:
        # Попытка декодирования JSON
        response_data = json.loads(html)
        if "msg" not in response_data:
            logger.error(
                f"Поле 'msg' отсутствует в ответе для заказа {orderno}.")
            return json.dumps({"error": "Invalid response format"}, ensure_ascii=False)

        # Извлечение HTML из поля 'msg'
        raw_html = response_data["msg"]
        logger.info(
            f"Сиб-Экспресс. Извлеченный HTML для заказа {orderno}: {raw_html}")
    except json.JSONDecodeError:
        logger.error(f"Ответ для заказа {orderno} не является валидным JSON.")
        return json.dumps({"error": "Invalid JSON response"}, ensure_ascii=False)

    try:
        # Парсинг HTML
        soup = BeautifulSoup(raw_html, 'lxml')

        # Проверка на отсутствие данных
        if "Не найдено" in raw_html:
            logger.error(f"Ответ не содержит данных для заказа {orderno}.")
            return json.dumps({"error": "Order not found"}, ensure_ascii=False)

        # Извлечение данных из таблицы
        data = {}

        # Поиск таблицы или строки с информацией
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    data[key] = value
        else:
            logger.error(
                f"Таблица с деталями не найдена для заказа {orderno}.")
            return {"error": "Detail table not found"}

        # Логирование и возврат результата
        logger.info(
            f"Сиб-Экспресс. Полученные данные для заказа {orderno}: {data}")
        return data
    except Exception as e:
        logger.error(f"Ошибка при обработке заказа {orderno}: {e}")
        return {"error": str(e)}


def parse_plex_post(html, orderno):
    try:
        # Парсим HTML
        soup = BeautifulSoup(html, "html.parser")

        # Ищем блок с классом panel-body
        panel_body = soup.find("div", class_="panel-body")
        if not panel_body:
            logger.error("Не найдена область с информацией о статусах.")
            return []

        # Собираем события
        events = []
        strong_tags = panel_body.find_all("strong")  # Ищем все теги <strong>
        for tag in strong_tags:
            date = tag.text.strip()  # Извлекаем текст внутри <strong>
            if tag.next_sibling and isinstance(tag.next_sibling, str):
                status = tag.next_sibling.strip(" -").strip()
                events.append({
                    "Дата": date,
                    "Статус": status
                })

        logger.info(f"""Плекс Пост. Полученные данные для заказа {
            orderno}: {events}""")
        return events

    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML: {e}")
        return []


"""
def parse_vip_mail_ufa(html, orderno):
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Находим таблицу с данными
        table = soup.find("table", class_="show_tracks")
        if not table:
            logger.error("Таблица с информацией об отслеживании не найдена.")
            return []

        rows = table.find("tbody").find_all("tr")  # Извлекаем строки таблицы
        events = []
        for row in rows:
            cols = row.find_all("td")  # Разбиваем строки на столбцы
            if len(cols) >= 3:
                date = cols[0].get_text(strip=True)
                status = cols[1].get_text(strip=True)
                notes = cols[2].get_text(strip=True)
                events.append(
                    {"Дата": date, "Статус": status, "Примечания": notes})

        return events
    except Exception as e:
        logger.error(
            f"ВипМайл Уфа. Ошибка при парсинге HTML для заказа {orderno}: {e}")
        return []"""
