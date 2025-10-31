from pathlib import Path
import os
from peewee import SqliteDatabase, Proxy
from loguru import logger

# Глобальный прокси для базы данных
db_proxy = Proxy()


def init_db(db_path: str = "data/city_expert.db") -> None:
    """
    Полная инициализация базы данных SQLite с расширенным логированием.

    Этапы работы:
    1. Подготовка директории для БД
    2. Настройка соединения с SQLite
    3. Инициализация прокси-подключения
    4. Создание таблиц моделей

    Args:
        db_path: Путь к файлу БД (по умолчанию 'data/city_expert.db')

    Raises:
        PermissionError: Нет прав на запись в директорию
        OperationalError: Ошибки SQLite
        Exception: Другие критические ошибки
    """
    logger.info("Starting database initialization", db_path=db_path)

    try:
        # 1. Подготовка директории
        logger.debug("Preparing database directory...")
        db_dir = Path(db_path).absolute().parent
        prepare_db_directory(db_dir)

        # 2. Настройка SQLite
        logger.debug("Configuring SQLite connection...")
        db = configure_sqlite(db_path)

        # 3. Инициализация прокси
        logger.debug("Initializing database proxy...")
        db_proxy.initialize(db)

        # 4. Создание таблиц
        logger.info("Creating database tables...")
        created_tables = create_tables()

        logger.success("Database initialized successfully",
                       tables_created=created_tables,
                       db_path=db_path)

    except PermissionError as pe:
        logger.critical("Database initialization failed: permission denied",
                        error=str(pe),
                        db_path=db_path)
        raise
    except Exception as e:
        logger.error("Database initialization failed",
                     error=str(e),
                     exc_info=True)
        raise


def prepare_db_directory(db_dir: Path) -> None:
    """Создает и проверяет директорию для БД."""
    logger.debug("Preparing database directory", directory=str(db_dir))

    try:
        if not db_dir.exists():
            logger.info("Creating database directory", directory=str(db_dir))
            db_dir.mkdir(parents=True, exist_ok=True)

        if not os.access(db_dir, os.W_OK):
            error_msg = f"No write permissions for directory: {db_dir}"
            logger.error("Directory permission error",
                         error=error_msg,
                         directory=str(db_dir))
            raise PermissionError(error_msg)

        logger.debug("Directory ready", directory=str(db_dir))

    except Exception as e:
        logger.error("Failed to prepare database directory",
                     directory=str(db_dir),
                     error=str(e),
                     exc_info=True)
        raise


def configure_sqlite(db_path: str) -> SqliteDatabase:
    """Создает и настраивает соединение с SQLite."""
    logger.debug("Configuring SQLite database", db_path=db_path)

    try:
        db = SqliteDatabase(
            db_path,
            pragmas={
                'journal_mode': 'wal',
                'cache_size': -1024 * 64,
                'foreign_keys': 1,
                'synchronous': 0,
                'temp_store': 'memory',
                'locking_mode': 'exclusive'
            }
        )
        logger.debug("SQLite configured successfully", db_path=db_path)
        return db

    except Exception as e:
        logger.error("Failed to configure SQLite",
                     db_path=db_path,
                     error=str(e),
                     exc_info=True)
        raise


def create_tables() -> list:
    """Создает таблицы моделей в БД и возвращает список созданных таблиц."""
    logger.debug("Starting table creation process")

    try:
        # Ленивый импорт для избежания циклических зависимостей
        from .user_model import User, FavoritePlace
        from .search_model import SearchModel

        tables = [User, FavoritePlace, SearchModel]
        created_tables = []

        with db_proxy.connection_context():
            existing_tables = db_proxy.get_tables()

            for model in tables:
                table_name = model.__name__.lower() + "s"
                if table_name not in existing_tables:
                    db_proxy.create_tables([model])
                    created_tables.append(table_name)
                    logger.debug("Table created", table=table_name)
                else:
                    logger.debug("Table already exists", table=table_name)

        logger.info("Table creation completed",
                    tables_created=created_tables,
                    total_tables=len(tables))
        return created_tables

    except Exception as e:
        logger.error("Failed to create tables",
                     error=str(e),
                     exc_info=True)
        raise


def close_db() -> None:
    """Безопасно закрывает соединение с БД."""
    logger.info("Closing database connection")

    try:
        if db_proxy.is_initialized() and not db_proxy.is_closed():
            db_proxy.close()
            logger.success("Database connection closed successfully")
        else:
            logger.debug("Database connection already closed or not initialized")
    except Exception as e:
        logger.error("Failed to close database connection",
                     error=str(e),
                     exc_info=True)
        raise