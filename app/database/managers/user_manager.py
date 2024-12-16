from sqlalchemy import exists
from database.models.user import User  
import uuid
from database.db_globals import Session

class UserManager:
    def __init__(self):
        self.Session = Session

    def add_user_password(self, username, password, auth_type='password'):
        """Добавляем пользователя стандартно"""
        session = self.Session()
        id = str(uuid.uuid4())
        new_user = User(id=id, user_id=username, auth_type=auth_type)
        new_user.set_password(password)  # Устанавливаем хэш пароля
        session.add(new_user)
        session.commit()
        session.close()

    def check_password(self, username, password):
        """Проверяем пароль пользователя"""
        session = self.Session()
        user = session.query(User).filter_by(user_id=username).first()
        session.close()
        if user and user.check_password(password):
            return True
        return False

    def update_user_password(self, username, new_password):
        """Обновляем пароль пользователя"""
        session = self.Session()
        user = session.query(User).filter_by(user_id=username).first()
        if user:
            user.set_password(new_password)  # Обновляем хэш пароля
            session.commit()
        session.close()


    def user_exists(self, username):
        """Проверка существования пользователя по имени"""
        session = self.Session()
        exists_query = session.query(exists().where(User.user_id == username)).scalar()
        session.close()
        return exists_query
    
    
    
    def delete_user_by_username(self, username):
        """Удалить пользователя с заданным user_id"""
        session=self.Session()
        try:
            # Находим пользователя по user_id
            user = session.query(User).filter_by(user_id=username).first()

            if user:
                # Если пользователь найден, удаляем его
                session.delete(user)
                session.commit()
                return True  # Возвращаем True, если пользователь был успешно удален
            else:
                return False  # Возвращаем False, если пользователь не найден

        except Exception as e:
            session.rollback()  # Откатываем изменения, если что-то пошло не так
            print(f"Ошибка при удалении пользователя: {e}")
            return False  # Возвращаем False при ошибке

        finally:
            session.close()  # Закрываем сессию


    def get_user_id_by_username(self, username):
        session=self.Session()
        try:
            user = session.query(User).filter_by(user_id=username).first()
            user_id=user.id
            return user_id
        finally:
            session.close()
