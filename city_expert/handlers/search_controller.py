from typing import Optional
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters as ft,
    CallbackQueryHandler,
    Application,
)
from loguru import logger
from city_expert.services.places_api import Place, PlacesAPI
from city_expert.models import User, SearchModel, FavoritePlace
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2


class SearchController:
    """Основной контроллер для обработки команд и поиска мест в Telegram боте."""

    def __init__(self, app: Application, api: PlacesAPI):
        """
        Инициализация контроллера.

        Args:
            app: Экземпляр Application из python-telegram-bot
            api: API для поиска мест
        """
        self.app = app
        self.api = api
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Регистрирует обработчики команд и сообщений."""
        handlers = [
            CommandHandler("start", self._start),
            CommandHandler("help", self._help),
            CommandHandler("history", self._show_history),
            CommandHandler("favorites", self._show_favorites),
            MessageHandler(ft.Text(["📍 Рядом со мной"]), self._search_nearby),
            MessageHandler(ft.Text(["📖 История поиска"]), self._show_history),
            MessageHandler(ft.Text(["❓ Помощь"]), self._help),
            MessageHandler(ft.Text(["🔍 Поиск достопримечательностей"]), self._start_search),
            MessageHandler(ft.Text(["↩️ Назад в меню"]), self._back_to_menu),
            MessageHandler(ft.LOCATION, self._handle_location),
            CallbackQueryHandler(self._handle_button_click, pattern="^(map|fav|unfav):"),
            MessageHandler(ft.TEXT & ~ft.COMMAND, self._handle_text_search),
        ]
        for handler in handlers:
            self.app.add_handler(handler)

    @staticmethod
    def _get_main_keyboard() -> ReplyKeyboardMarkup:
        """ Создает основную клавиатуру меню с главными командами.

        Returns:
            ReplyKeyboardMarkup: Клавиатура с кнопками:
                - Рядом со мной
                - История поиска
                - Помощь
                - Поиск достопримечательностей
        """

        return ReplyKeyboardMarkup(
            [
                [KeyboardButton("📍 Рядом со мной"), KeyboardButton("📖 История поиска")],
                [KeyboardButton("❓ Помощь"), KeyboardButton("🔍 Поиск достопримечательностей")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,  # Скрывает клавиатуру после использования
        )

    @staticmethod
    def _get_location_keyboard() -> ReplyKeyboardMarkup:
        """ Создает клавиатуру для запроса геолокации.

        Returns:
            ReplyKeyboardMarkup: Клавиатура с кнопками:
                - Отправить геопозицию (с запросом локации)
                - Назад в меню
        """

        return ReplyKeyboardMarkup(
            [
                [KeyboardButton("📍 Отправить геопозицию", request_location=True)],
                [KeyboardButton("↩️ Назад в меню")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    @staticmethod
    async def _start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """ Обрабатывает команду /start - приветствие пользователя.

        Args:
            update (Update): Объект обновления Telegram
        """

        await update.message.reply_text(
            "👋 Привет! Я бот для поиска мест.\nВыберите действие с помощью меню ниже 👇",
            reply_markup=SearchController._get_main_keyboard(),
        )

    @staticmethod
    async def _help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help."""
        help_text = (
            "📌 Доступные команды:\n"
            "/start - Начало работы\n"
            "/help - Эта справка\n"
            "/history - История поиска\n"
            "/favorites - Избранные места\n\n"
            "Просто отправьте название места для поиска!"
        )
        await update.message.reply_text(
            help_text, reply_markup=SearchController._get_main_keyboard()
        )

    @staticmethod
    async def _search_nearby(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """ Обрабатывает запрос поиска мест рядом с пользователем.

        Args:
            update (Update): Объект обновления Telegram
        """

        await update.message.reply_text(
            "📍 Отправьте свою геопозицию для поиска рядом!",
            reply_markup=SearchController._get_location_keyboard(),
        )

    @staticmethod
    async def _back_to_menu(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик кнопки 'Назад в меню'."""
        await update.message.reply_text(
            "🏠 Вы вернулись в главное меню.",
            reply_markup=SearchController._get_main_keyboard(),
        )

    @staticmethod
    async def _start_search(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик кнопки 'Поиск достопримечательностей'.
        Args:
            update (Update): Объект обновления Telegram
        """
        await update.message.reply_text(
            "🔍 Просто напишите название места или отправьте местоположение!",
            reply_markup=SearchController._get_main_keyboard(),
        )

    async def _show_favorites(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает избранные места пользователя.
        Args:
            update (Update): Объект обновления Telegram
        """
        try:
            # Получаем или создаем пользователя
            user = User.get_or_create(
                telegram_id=update.effective_user.id,
                defaults={
                    "full_name": update.effective_user.full_name,
                    "username": update.effective_user.username,
                },
            )[0]

            # Получаем избранные места (последние добавленные сначала)
            favorites = FavoritePlace.select().where(
                FavoritePlace.user == user
            ).order_by(FavoritePlace.added_at.desc())

            if not favorites:
                await update.message.reply_text(
                    "У вас пока нет избранных мест",
                    reply_markup=self._get_main_keyboard(),
                )
                return

            # Формируем ответ с HTML-разметкой
            response = "⭐ <b>Избранные места:</b>\n\n"
            for fav in favorites:
                response += (
                    f"🏛 <b>{fav.name}</b>\n"
                    f"📅 Добавлено: {fav.added_at.strftime('%d.%m.%Y')}\n"
                    f"📍 <a href='https://www.google.com/maps?q={fav.place_id}'>Показать на карте</a>\n\n"
                )

            await update.message.reply_text(
                response,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=self._get_main_keyboard(),
            )

        except Exception as e:
            logger.error(f"Favorites error: {e}")
            await update.message.reply_text(
                "⚠️ Ошибка при получении избранных мест",
                reply_markup=self._get_main_keyboard(),
            )

    async def _handle_button_click(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает нажатия inline-кнопок (карта, избранное).

        Args:
            update (Update): Объект обновления Telegram
        """
        query = update.callback_query
        await query.answer()

        try:
            if not query.data or ":" not in query.data:
                raise ValueError("Неверный формат callback данных")

            # Разбираем данные callback_data (формат: "action:param1:param2")

            action, *payload = query.data.split(":")
            user = User.get(telegram_id=query.from_user.id)

            if action == "map":
                lat, lon = payload[0].split(",")
                maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                await query.message.reply_text(
                    f"📍 Открыть в Google Maps:\n{maps_url}",
                    disable_web_page_preview=True
                )

            elif action in ("fav", "unfav"):
                # Обработка кнопок избранного
                coords, name = payload[0], ":".join(payload[1:])
                lat, lon = coords.split(",")
                place_id = f"{lat},{lon}"

                if action == "fav":
                    # Добавляем место в избранное
                    FavoritePlace.create(
                        user=user,
                        place_id=place_id,
                        name=name,
                        added_at=datetime.now()
                    )
                    # Обновляем кнопку на "Удалить из избранного"
                    await query.edit_message_reply_markup(
                        reply_markup=self._create_place_keyboard(place_id, name, user, True)
                    )
                else:
                    # Удаляем место из избранного
                    FavoritePlace.delete().where(
                        (FavoritePlace.user == user) &
                        (FavoritePlace.place_id == place_id)
                    ).execute()
                    # Обновляем кнопку на "Добавить в избранное"

                    await query.edit_message_reply_markup(
                        reply_markup=self._create_place_keyboard(place_id, name, user, False)
                    )

        except Exception as e:
            logger.error(f"Button click error: {e}")
            await query.message.reply_text("⚠️ Произошла ошибка")

    async def _handle_location(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает получение геолокации от пользователя.

        Args:
            update (Update): Объект обновления Telegram
        """
        if not update.message or not update.message.location:
            await update.message.reply_text("Не удалось получить ваше местоположение")
            return

        location = update.message.location
        user_id = update.effective_user.id
        logger.info(f"Получена геолокация от пользователя {user_id}: {location.latitude}, {location.longitude}")

        try:
            # Получаем или создаем пользователя
            User.get_or_create(
                telegram_id=user_id,
                defaults={
                    "full_name": update.effective_user.full_name,
                    "username": update.effective_user.username,
                },
            )

            await update.message.reply_text("🔍 Ищу интересные места рядом...")
            places = await self.api.search(
                "достопримечательности",
                latitude=location.latitude,
                longitude=location.longitude,
                user_id=user_id,
            )

            if not places:
                await update.message.reply_text("😕 Рядом не найдено интересных мест")
                return

            for place in places[:3]:
                await self._send_place_result(update, place, location)

        except Exception as e:
            logger.error(f"Location search error: {e}")
            await update.message.reply_text("⚠️ Ошибка при поиске мест рядом")

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Вычисляет расстояние между двумя точками в метрах
        по формуле гаверсинусов.
        Args:
            lat1 (float): Широта первой точки
            lon1 (float): Долгота первой точки
            lat2 (float): Широта второй точки
            lon2 (float): Долгота второй точки

        Returns:
            float: Расстояние в метрах

        """
        earth_radius_m = 6371000 # Радиус Земли в метрах
        # Конвертируем градусы в радианы
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Разница координат
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Формула гаверсинусов
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return earth_radius_m * 2 * atan2(sqrt(a), sqrt(1 - a))

    async def _show_history(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает историю поиска пользователя."""
        try:
            # Получаем или создаем пользователя
            user = User.get_or_create(
                telegram_id=update.effective_user.id,
                defaults={
                    "full_name": update.effective_user.full_name,
                    "username": update.effective_user.username,
                },
            )[0]

            # Получаем последние 10 запросов
            history = SearchModel.select().where(
                SearchModel.user == user
            ).order_by(SearchModel.created_at.desc()).limit(10)

            # Формируем ответ
            if not history.exists():
                await update.message.reply_text(
                    "История поиска пуста",
                    reply_markup=self._get_main_keyboard()
                )
                return

            response = "📖 <b>История поиска:</b>\n\n"
            for item in history:
                response += f"🔍 {item.query}\n🕒 {item.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

            await update.message.reply_text(
                response,
                parse_mode="HTML",
                reply_markup=self._get_main_keyboard()
            )

        except Exception as e:
            logger.error(f"History error: {e}")
            await update.message.reply_text(
                "⚠️ Ошибка при получении истории",
                reply_markup=self._get_main_keyboard(),
            )

    async def _handle_text_search(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает текстовый запрос на поиск мест."""
        query = update.message.text.strip()
        if len(query) < 2:
            await update.message.reply_text("Слишком короткий запрос")
            return

        await update.message.reply_text("🔍 Ищу места...")

        try:
            user = User.get_or_create(
                telegram_id=update.effective_user.id,
                defaults={
                    "full_name": update.effective_user.full_name,
                    "username": update.effective_user.username,
                },
            )[0]

            # Выполняем поиск через API
            places = await self.api.search(query, user_id=user.telegram_id)

            # Сохраняем запрос в историю
            SearchModel.create(
                user=user,
                query=query,
                results_count=len(places) if places else 0,
                created_at=datetime.now(),
                is_location_search=False,
            )

            if not places:
                await update.message.reply_text("Ничего не найдено")
                return

            for place in places[:5]:
                await self._send_place_result(update, place)

        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text("⚠️ Ошибка при поиске")

    @staticmethod
    def _create_place_keyboard(place_id: str, name: str, is_favorite: bool) -> InlineKeyboardMarkup:
        """ Создает inline-клавиатуру для взаимодействия с местом.

        Args:
            place_id (str): Идентификатор места
            name (str): Название места
            is_favorite (bool): В избранном ли место

        Returns:
            InlineKeyboardMarkup: Объект клавиатуры
        """

        buttons = [
            InlineKeyboardButton(
                "🗺 Карта",
                callback_data=f"map:{place_id}"
            ),
            InlineKeyboardButton(
                "⭐ Удалить" if is_favorite else "🌟 Добавить",
                callback_data=f"{'unfav' if is_favorite else 'fav'}:{place_id}:{name[:30]}"
            )
        ]
        return InlineKeyboardMarkup([buttons])

    @staticmethod
    def _create_place_keyboard(place_id: str, name: str, is_favorite: bool) -> InlineKeyboardMarkup:
        """Создает клавиатуру для места.
        Args:
            place_id: Идентификатор места в формате "lat,lon"
            name: Название места (обрезается до 30 символов)
            is_favorite: Флаг, находится ли место в избранном

        Returns:
            InlineKeyboardMarkup: Клавиатура с кнопками:
                - "🗺 Карта" - открывает карту
                - "⭐ Удалить"/"🌟 Добавить" - управление избранным
        """
        buttons = [
            InlineKeyboardButton(
                "🗺 Карта",
                callback_data=f"map:{place_id}"
            ),
            InlineKeyboardButton(
                "⭐ Удалить" if is_favorite else "🌟 Добавить",
                callback_data=f"{'unfav' if is_favorite else 'fav'}:{place_id}:{name[:30]}"
            )
        ]
        return InlineKeyboardMarkup([buttons])

    async def _handle_callback_query(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает callback-запросы от inline-кнопок (карта/избранное).

        Args:
            update: Объект Update от Telegram API
            _: Неиспользуемый контекст (заменен на _)
        """
        query = update.callback_query
        await query.answer()  # Обязательное подтверждение получения callback

        try:
            if not query.data:
                raise ValueError("Отсутствуют callback данные")

            # Разбор данных формата "action:param1:param2:..."
            action, *payload = query.data.split(":")

            if action == "map":
                # Обработка кнопки "Карта"
                if not payload or len(payload[0].split(",")) != 2:
                    raise ValueError("Неверный формат координат")

                lat, lon = payload[0].split(",")
                await query.message.reply_text(
                    f"📍 Открыть в Google Maps:\nhttps://www.google.com/maps?q={lat},{lon}",
                    disable_web_page_preview=True
                )

            elif action in ("fav", "unfav"):
                # Обработка избранного
                if not payload:
                    raise ValueError("Недостаточно данных для обработки избранного")

                user = User.get(telegram_id=query.from_user.id)
                place_id = payload[0]
                name = ":".join(payload[1:]) if len(payload) > 1 else "Место"

                if action == "fav":
                    FavoritePlace.create(
                        user=user,
                        place_id=place_id,
                        name=name,
                        added_at=datetime.now()
                    )
                else:
                    FavoritePlace.delete().where(
                        (FavoritePlace.user == user) &
                        (FavoritePlace.place_id == place_id)
                    ).execute()

                # Обновляем только клавиатуру
                await query.edit_message_reply_markup(
                    reply_markup=self._create_place_keyboard(
                        place_id=place_id,
                        name=name,
                        is_favorite=action == "fav"
                    )
                )

        except ValueError as e:
            logger.warning(f"Некорректные callback данные: {e}")
            await query.message.reply_text("⚠️ Некорректный запрос")
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            await query.message.reply_text(
                "⚠️ Ошибка при обработке запроса",
                reply_markup=self._get_main_keyboard()
            )


    async def _send_place_result(self, update: Update, place: Place, user_location: Optional[Place] = None) -> None:
        """Отправляет пользователю информацию о найденном месте.

        Args:
            update (Update): Объект обновления от Telegram API
            place (Place): Найденное место
            user_location (Optional[Place]): Локация пользователя (необязательно)
        """

        try:
            user = User.get(telegram_id=update.effective_user.id)

            # Формируем текст сообщения
            message_text = (
                f"📍 <b>{place.name}</b>\n"
                f"📌 <i>{place.address}</i>\n"
                f"⭐ Рейтинг: {place.rating or 'нет'}\n"
            )

            # Добавляем расстояние, если известна локация пользователя
            if user_location:
                distance = self._calculate_distance(
                    user_location.latitude,
                    user_location.longitude,
                    place.latitude,
                    place.longitude
                )
                message_text += f"🚶‍♂️ ~{int(distance)} м от вас\n"

            # Добавляем контактную информацию
            if place.website:
                message_text += f"🌐 <a href='{place.website}'>Сайт</a>\n"
            if place.phone:
                message_text += f"📞 Телефон: {place.phone}\n"

            # Создаем идентификатор места
            place_id = f"{place.latitude:.6f},{place.longitude:.6f}"

            # Проверяем, есть ли место в избранном
            is_favorite = FavoritePlace.select().where(
                (FavoritePlace.user == user) &
                (FavoritePlace.place_id == place_id)
            ).exists()

            # Создаем клавиатуру
            keyboard = self._create_place_keyboard(place_id, place.name, user, is_favorite)

            photo_url = next(
                (p for p in place.photos if isinstance(p, str) and p.startswith(('http://', 'https://'))),
                None
            )

            # Пытаемся отправить фото
            if photo_url:
                try:
                    await update.message.reply_photo(
                        photo=photo_url,
                        caption=message_text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    return
                except Exception as e:
                    logger.warning(f"Не удалось отправить фото: {e}")

            # Если фото нет или не удалось отправить - отправляем текст
            await update.message.reply_text(
                message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        except Exception as e:
            logger.error(f"Ошибка отправки места: {e}")