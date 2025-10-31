from peewee import SqliteDatabase
from pathlib import Path

from city_expert.models import User, SearchModel
import logging

# Инициализация логгера для работы с базой данных
logger = logging.getLogger("database")

# Создание экземпляра SQLite базы данных (пока без подключения)
db = SqliteDatabase(None)


def init_db(db_path: str = "data/city_expert.db") -> None:
    """
    Инициализирует и подключает базу данных SQLite с автоматическим созданием:
    - Родительских директорий для файла БД
    - Таблиц моделей (если их не существует)

    Args:
        db_path (str): Относительный/абсолютный путь к файлу БД

    Raises:
        OperationalError: При проблемах подключения к БД
        RuntimeError: При других критических ошибках
    """
    try:
        # Создание директорий для БД (если не существуют)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Инициализация подключения к БД
        db.init(db_path)

        # Переподключение для гарантии рабочего соединения
        if not db.is_closed():
            db.close()
        db.connect()

        # Создание таблиц с безопасным режимом
        db.create_tables([User, SearchModel], safe=True)
        logger.info(f"✅ База данных успешно инициализирована: {db_path}")

    except Exception as e:
        logger.error(f"❌ Ошибка базы данных: {str(e)}")
        raise
