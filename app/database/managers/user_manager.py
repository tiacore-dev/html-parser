import uuid
from sqlalchemy import exists
from app.database.models import User
from app.database.db_globals import Session


class UserManager:
    def __init__(self):
        self.Session = Session

    def add_user(self, username, password):
        """Добавляем пользователя стандартно"""
        session = self.Session()
        try:
            id = str(uuid.uuid4())
            new_user = User(user_id=id, login=username)
            new_user.set_password(password)  # Устанавливаем хэш пароля
            session.add(new_user)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ошибка при добавлении пользователя: {e}")
        finally:
            session.close()

    def check_password(self, username, password):
        """Проверяем пароль пользователя"""
        session = self.Session()
        try:
            user = session.query(User).filter_by(login=username).first()
            if user and user.check_password(password):
                return True
            return False
        except Exception as e:
            print(f"Ошибка при проверке пароля: {e}")
            return False
        finally:
            session.close()

    def update_user_password(self, username, new_password):
        """Обновляем пароль пользователя"""
        session = self.Session()
        try:
            user = session.query(User).filter_by(login=username).first()
            if user:
                user.set_password(new_password)  # Обновляем хэш пароля
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ошибка при обновлении пароля: {e}")
        finally:
            session.close()

    def user_exists(self, username):
        """Проверка существования пользователя по имени"""
        session = self.Session()
        try:
            exists_query = session.query(
                exists().where(User.login == username)).scalar()
            return exists_query
        except Exception as e:
            session.rollback()
            print(f"Ошибка при поиске пользователя: {e}")
            return False
        finally:
            session.close()

    def delete_user_by_username(self, username):
        """Удалить пользователя с заданным username"""
        session = self.Session()
        try:
            user = session.query(User).filter_by(login=username).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            else:
                return False
        except Exception as e:
            session.rollback()
            print(f"Ошибка при удалении пользователя: {e}")
            return False
        finally:
            session.close()

    def get_user_id_by_username(self, username):
        """Получить user_id по username"""
        session = self.Session()
        try:
            user = session.query(User).filter_by(login=username).first()
            if user:
                return user.user_id
            else:
                return None
        except Exception as e:
            print(f"Ошибка при получении user_id: {e}")
            return None
        finally:
            session.close()
