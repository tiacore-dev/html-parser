from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database.db_setup import Base


class Logs(Base):
    __tablename__ = "logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    # Действие, которое было выполнено
    action = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)  # Сообщение лога
    timestamp = Column(DateTime, default=datetime.utcnow)  # Дата и время

    # Связи
    def to_dict(self):
        """Преобразование объекта лога в словарь."""
        return {
            "id": self.log_id,
            "action": self.action,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),  # Форматируем дату для JSON
        }
