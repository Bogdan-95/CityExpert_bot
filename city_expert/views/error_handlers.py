
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from typing import Optional
from enum import Enum, auto
from city_expert.utils.config_loader import config

# ID чата администратора для критических уведомлений
ADMIN_CHAT_ID = config.ADMIN_CHAT_ID


class ErrorType(Enum):
    """Перечисление типов ошибок для классификации и обработки"""
    DATABASE = auto()  # Ошибки базы данных
    API = auto()  # Ошибки внешних API
    VALIDATION = auto()  # Ошибки валидации данных
    NETWORK = auto()  # Проблемы с сетью
    UNKNOWN = auto()  # Неизвестные ошибки


class ErrorHandler:
    """Основной класс для обработки и логирования ошибок бота"""

    # Сообщения и теги для разных типов ошибок
    ERROR_MESSAGES = {
        ErrorType.DATABASE: (
            "⚠️ Ошибка при работе с базой данных. Попробуйте позже.",
            "database_error",
        ),
        ErrorType.API: (
            "⚠️ Сервис поиска временно недоступен. Попробуйте позже.",
            "api_error",
        ),
        ErrorType.VALIDATION: (
            "❌ Некорректный ввод. Пожалуйста, проверьте данные.",
            "validation_error",
        ),
        ErrorType.NETWORK: (
            "⚠️ Проблемы с интернет-соединением. Проверьте подключение.",
            "network_error",
        ),
        ErrorType.UNKNOWN: (
            "⚠️ Произошла непредвиденная ошибка. Разработчики уже уведомлены.",
            "unknown_error",
        ),
    }

    @staticmethod
    async def handle(
            update: Update,
            _: ContextTypes.DEFAULT_TYPE,
            error: Exception,
            error_type: Optional[ErrorType] = None,
    ) -> None:
        """
        Основной метод обработки ошибок.

        Args:
            update: Объект Update от Telegram
            _: Неиспользуемый контекст обработчика
            error: Возникшее исключение
            error_type: Опциональный тип ошибки (если None - определяется автоматически)
        """
        try:
            # Определяем тип ошибки, если не указан
            error_type = error_type or ErrorHandler.detect_error_type(error)
            # Получаем сообщение для пользователя и тег для логов
            message, log_tag = ErrorHandler.ERROR_MESSAGES[error_type]

            # Логируем ошибку с дополнительным контекстом
            logger.opt(lazy=True).error(
                "[{tag}] Error in update {update_id}: {error}",
                tag=log_tag,
                update_id=lambda: update.update_id if update else None,
                error=lambda: str(error),
            )

            # Отправляем сообщение пользователю, если возможно
            if update and update.effective_message:
                from city_expert.views.keyboards import get_main_keyboard
                await update.effective_message.reply_text(
                    message,
                    reply_markup=get_main_keyboard()
                )

        except Exception as handler_error:
            # Логируем критические ошибки в самом обработчике
            logger.critical(f"CRITICAL: Error handler failure: {handler_error}")

    @staticmethod
    def detect_error_type(error: Exception) -> ErrorType:
        """
        Автоматически определяет тип ошибки на основе её содержимого.

        Args:
            error: Исключение для анализа

        Returns:
            ErrorType: Определенный тип ошибки
        """
        error_str = str(error).lower()

        # Определяем тип по ключевым словам в сообщении об ошибке
        if any(db_word in error_str for db_word in ["database", "sql", "query", "sqlite"]):
            return ErrorType.DATABASE
        elif any(api_word in error_str for api_word in ["api", "http", "request", "response"]):
            return ErrorType.API
        elif any(net_word in error_str for net_word in ["connection", "network", "timeout", "socket"]):
            return ErrorType.NETWORK
        elif any(val_word in error_str for val_word in ["validation", "invalid", "validate", "value"]):
            return ErrorType.VALIDATION

        return ErrorType.UNKNOWN


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Глобальный обработчик ошибок для Telegram бота.

    Args:
        update: Объект Update или любой другой объект
        context: Контекст обработчика с информацией об ошибке
    """
    try:
        # Проверяем, что это действительно Update от Telegram
        if not isinstance(update, Update):
            logger.error("Received error without Update object")
            return

        # Делегируем обработку основному классу
        await ErrorHandler.handle(update, context, context.error)

    except Exception as e:
        # Логируем критические ошибки в глобальном обработчике
        logger.critical(f"FATAL: Global error handler failure: {e}")

        # Пытаемся уведомить администратора, если бот доступен
        if context.bot and hasattr(context.bot, "send_message"):
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"🔥 Critical bot error: {str(e)[:1000]}",  # Ограничиваем длину сообщения
            )