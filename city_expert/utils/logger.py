
from loguru import logger
import sys
import json
from typing import Dict, Any

def setup_logger() -> None:
    """
    Настройка логгера с двумя обработчиками:
    1. Консольный вывод с цветным форматированием для удобства чтения в терминале.
    2. Запись логов в файл в формате JSON с ротацией и сжатием.

    Также добавляется пользовательский уровень логирования SUCCESS (если он ещё не добавлен).
    """
    # Удаляем все существующие обработчики, чтобы избежать дублирования
    logger.remove()

    # 1. Консольный обработчик
    logger.add(
        sink=sys.stdout,  # Вывод в стандартный поток вывода (консоль)
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),  # Форматирование с цветами для удобства чтения
        level="DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 2. Файловый обработчик с JSON-логами
    logger.add(
        sink="logs/bot.log",
        serialize=True,
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
        enqueue=True,
        catch=True,
        format="{message}"
    )

    # Добавляем кастомный уровень SUCCESS, если его ещё нет
    try:
        logger.level("SUCCESS", no=25, color="<green>", icon="✅")
    except TypeError:
        # Если уровень уже существует, игнорируем ошибку
        pass


def serialize_record(record: Dict[str, Any]) -> str:
    """
    Сериализация записи лога в JSON строку.

    Используется для ручной сериализации, если в обработчике не используется параметр serialize=True.

    Args:
        record (Dict[str, Any]): Словарь с данными лога, который передает Loguru.

    Returns:
        str: JSON-строка с сериализованными данными лога.
    """
    try:
        log_data = {
            "timestamp": record["time"].timestamp(),  # Временная метка в формате UNIX timestamp
            "level": record["level"].name,             # Уровень логирования (DEBUG, INFO, ERROR и т.д.)
            "message": record["message"],              # Текст сообщения лога
            "module": record["module"],                # Модуль, откуда вызван лог
            "function": record["function"],            # Функция, откуда вызван лог
            "line": record["line"],                    # Номер строки в исходном коде
            "process": record["process"].id,           # ID процесса
            "thread": record["thread"].name,           # Имя потока
        }

        # Если в записи есть исключение, добавляем его в лог
        if "exception" in record and record["exception"]:
            log_data["exception"] = str(record["exception"])

        return json.dumps(log_data)

    except (TypeError, ValueError, KeyError) as e:
        # В случае ошибки сериализации возвращаем JSON с описанием ошибки
        return json.dumps({"error": f"Serialization error: {str(e)}"})
