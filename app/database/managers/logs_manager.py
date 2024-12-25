from datetime import timedelta, datetime
from app.database.models import Logs
from app.database.db_globals import Session
from sqlalchemy import or_


class LogManager:
    def __init__(self):
        self.Session = Session

    def add_logs(self, action, message):
        """Добавление лога."""
        session = self.Session()
        try:
            # Создаем объект Logs
            new_record = Logs(action=action, message=message)
            session.add(new_record)  # Добавляем новый лог через сессию
            session.commit()  # Не забудьте зафиксировать изменения в базе данных
            return new_record
        except Exception as e:
            session.rollback()  # Откат изменений в случае ошибки
            print(f"Ошибка при добавлении лога: {e}")
            return None
        finally:
            session.close()

    def get_logs_by_date(self, date, offset=0, limit=10):
        """Получение логов по дате."""
        session = self.Session()
        try:
            return session.query(Logs).filter(
                Logs.timestamp >= date,
                Logs.timestamp < date + timedelta(days=1)
            ).offset(offset).limit(limit).all()
        except Exception as e:
            print(f"Ошибка при получении логов по дате: {e}")
            return []
        finally:
            session.close()

    def filter_by_date(self, date=None, offset=0, limit=10):
        """Фильтрация логов по дате и ID пользователя."""
        session = self.Session()
        try:
            query = session.query(Logs)
            if date:
                # Конвертация строки даты в объект datetime
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                query = query.filter(
                    Logs.timestamp >= date_obj,
                    Logs.timestamp < date_obj + timedelta(days=1)
                )
            return query.offset(offset).limit(limit).all()
        except Exception as e:
            print(f"Ошибка при фильтрации логов: {e}")
            return []
        finally:
            session.close()

    def get_logs_paginated(self, date=None, search=None, offset=0, limit=10):
        """Получение логов с фильтрацией и пагинацией."""
        session = self.Session()
        try:
            query = session.query(Logs)

            # Фильтрация по дате, если указано
            if date:
                try:
                    # Конвертируем строку в дату
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    query = query.filter(
                        Logs.timestamp >= date_obj,
                        Logs.timestamp < date_obj + timedelta(days=1)
                    )
                except ValueError as exc:
                    raise ValueError(
                        "Некорректный формат даты. Ожидается формат 'YYYY-MM-DD'.") from exc
            if search:
                query = query.filter(
                    or_(
                        Logs.message.ilike(f"%{search}%"),
                        Logs.action.ilike(f"%{search}%")
                    )
                )
            total_count = query.count()  # Получаем общее количество записей
            # Получаем логи с учетом пагинации
            logs = query.offset(offset).limit(limit).all()

            # Форматируем логи в виде списка словарей
            result = [log.to_dict() for log in logs] if logs else []
            return result, total_count
        except Exception as e:
            print(f"Ошибка при получении логов с пагинацией: {e}")
            return [], 0
        finally:
            session.close()

    def get_logs(self, date=None):
        """Получение логов с фильтрацией."""
        session = self.Session()
        try:
            query = session.query(Logs)

            # Фильтрация по дате, если указано
            if date:
                try:
                    # Конвертируем строку в дату
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    query = query.filter(
                        Logs.timestamp >= date_obj,
                        Logs.timestamp < date_obj + timedelta(days=1)
                    )
                except ValueError as exc:
                    raise ValueError(
                        "Некорректный формат даты. Ожидается формат 'YYYY-MM-DD'.") from exc
            logs = query.all()  # Получаем логи

            # Форматируем логи в виде списка словарей
            result = [log.to_dict() for log in logs] if logs else []
            return result
        except Exception as e:
            print(f"Ошибка при получении логов: {e}")
            return []
        finally:
            session.close()
