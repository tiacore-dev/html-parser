from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_setup import Base 


class User(Base):
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, autoincrement=False)
    user_id = Column(String, unique=True, nullable=False)  # Email или другой уникальный идентификатор
    password_hash = Column(String, nullable=True)  # Может быть NULL для OAuth-пользователей
    google_id = Column(String, unique=True, nullable=True)  # Google ID для OAuth пользователей
    auth_type = Column(String, nullable=False, default='password')  # 'password' или 'google'

    def set_password(self, password):
        if self.auth_type == 'password':
            self.password_hash = generate_password_hash(password)
        else:
            raise ValueError("Cannot set password for this authentication type.")

    def check_password(self, password):
        if self.auth_type == 'password' and self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False