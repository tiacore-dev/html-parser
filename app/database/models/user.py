from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.db_setup import Base 


class User(Base):
    __tablename__ = 'users'

    user_id = Column(String(36), primary_key=True, autoincrement=False)
    login = Column(String, unique=True, nullable=False)  # Email или другой уникальный идентификатор
    password_hash = Column(String, nullable=True)  # Может быть NULL для OAuth-пользователей

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
