from app.database.db_setup import Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

class Logs(Base):
    __tablename__ = 'logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(255), nullable=False)  # Действие, которое было выполнено
    message = Column(Text, nullable=False)  # Сообщение лога
    timestamp = Column(DateTime, default=datetime.utcnow)  # Дата и время

    # Связи
    

    def to_dict(self):
        """Преобразование объекта лога в словарь."""
        return {
            "id": self.log_id,
            "action": self.action,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()  # Форматируем дату для JSON
        }
