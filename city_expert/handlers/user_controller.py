from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from loguru import logger
from city_expert.models import User


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        logger.info(f"Processing /start from user {user_id}")

        user, created = User.get_or_create(
            telegram_id=user_id,
            defaults={
                "username": update.effective_user.username,
                "full_name": update.effective_user.full_name,
            },
        )

        if created:
            logger.success(f"New user registered: {user_id}")
        else:
            logger.debug(f"Existing user: {user_id}")

        welcome_text = (
            "🌍 Добро пожаловать в CityExpert!\n\n"
            "Я помогу найти интересные места вокруг вас.\n"
            "Отправьте мне свою геолокацию или используйте команду /search"
        )
        await update.message.reply_text(welcome_text)

    except Exception as e:
        logger.error(f"Start error: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Ошибка при запуске бота")



async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /help.
    Отправляет пользователю справку по доступным командам.
    """
    help_text = (
        "📚 Доступные команды:\n\n"
        "/start - Перезапустить бота\n"
        "/help - Показать справку\n"
        "/search - Найти достопримечательности\n"
        "/history - История ваших запросов\n\n"
        "📍 Просто отправьте свою геолокацию для поиска мест рядом"
    )
    await update.message.reply_text(help_text)

def setup_handlers(app) -> None:
    """
    Регистрирует обработчики команд /start и /help в приложении Telegram Bot.
    Args:
        app: экземпляр приложения telegram.ext.Application
    """
    app.add_handler(CommandHandler("start", start))  # Обработчик команды /start
    app.add_handler(CommandHandler("help", help_command))  # Обработчик команды /help
