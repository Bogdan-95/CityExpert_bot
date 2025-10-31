from telegram.ext import ApplicationBuilder, Application
from loguru import logger
from city_expert.utils.config_loader import load_config
from city_expert.models.database import init_db
from city_expert.services.places_api import PlacesAPI
from city_expert.handlers.search_controller import SearchController
import asyncio
import sys


async def run_bot():
    """
    Основная асинхронная функция запуска бота.

    Последовательно выполняет:
    - загрузку конфигурации,
    - инициализацию базы данных,
    - создание клиента внешнего API,
    - построение и инициализацию Telegram-приложения,
    - регистрацию обработчиков,
    - запуск бота и его опроса (polling),
    - удержание процесса в активном состоянии.

    Обрабатывает исключения и корректно завершает работу.
    """
    try:
        logger.info("Starting bot initialization...")

        # Загружаем конфигурацию из файла или переменных окружения
        config = load_config()

        logger.debug("Initializing database...")
        # Инициализируем подключение к базе данных
        init_db()

        logger.info("Creating PlacesAPI client...")
        # Создаем асинхронный клиент для работы с внешним Places API
        async with PlacesAPI(config.RAPIDAPI_KEY) as api:
            logger.debug("Building Telegram application...")

            # Обработчик успешного запуска бота
            async def on_bot_startup(_: Application):
                logger.info("Bot initialized successfully")

            # Обработчик корректного завершения работы бота
            async def on_bot_shutdown(_: Application):
                logger.info("Bot shutdown completed")

            # Создаем приложение Telegram-бота с использованием токена и обработчиков событий
            app = (
                ApplicationBuilder()
                .token(config.TELEGRAM_BOT_TOKEN)
                .post_init(on_bot_startup)
                .post_shutdown(on_bot_shutdown)
                .build()
            )

            logger.debug("Registering handlers...")
            # Регистрируем контроллер, который добавляет обработчики команд и сообщений
            SearchController(app, api)

            logger.info("Starting bot...")
            # Инициализируем приложение (подключение к Telegram API)
            await app.initialize()

            # Запускаем polling - опрос Telegram сервера для получения обновлений
            if app.updater:
                logger.debug("Starting polling...")
                await app.updater.start_polling()

            # Запускаем приложение (бот становится активен)
            await app.start()
            logger.success("Bot is now running")

            # Удерживаем программу в активном состоянии, чтобы бот работал постоянно
            while True:
                await asyncio.sleep(3600)

    except asyncio.CancelledError:
        # Обработка сигнала отмены (например, при остановке приложения)
        logger.info("Bot received cancellation signal")
    except Exception as e:
        # Логируем критические ошибки и пробрасываем исключение дальше
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        raise
    finally:
        # Корректное завершение работы - закрываем соединения
        await shutdown()


async def shutdown():
    """Функция корректного завершения работы бота."""
    try:
        from city_expert.models.database import db_proxy
        if db_proxy.is_connection_usable():
            db_proxy.close()
        logger.info("All connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    finally:
        await asyncio.sleep(0.1)


def main():
    """
    Точка входа приложения.

    Создает и запускает новый асинхронный цикл событий,
    обрабатывает исключения и корректно завершает работу.
    """
    try:
        # Создаем новый цикл событий asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Запускаем основную асинхронную функцию бота
            loop.run_until_complete(run_bot())
        except KeyboardInterrupt:
            # Обработка прерывания пользователем (Ctrl+C)
            logger.info("Bot stopped by user")
        except Exception as e:
            # Логируем неожиданные ошибки
            logger.critical(f"Unexpected error: {e}")
        finally:
            # При завершении цикла событий корректно закрываем ресурсы
            if not loop.is_closed():
                loop.run_until_complete(shutdown())
                loop.close()
    except Exception as e:
        # Логируем ошибки и завершаем программу с кодом ошибки
        logger.critical(f"Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Запуск программы
    main()
