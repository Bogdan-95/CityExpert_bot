from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню с основными действиями"""
    return ReplyKeyboardMarkup(
        [
            ["🔍 Поиск достопримечательностей"],
            ["📍 Рядом со мной", "📖 История поиска"],
            ["❓ Помощь"],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_search_types_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора типа поиска"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🏛 Музеи", callback_data="search_type:museum"),
                InlineKeyboardButton("🌳 Парки", callback_data="search_type:park"),
            ],
            [
                InlineKeyboardButton(
                    "🍴 Рестораны", callback_data="search_type:restaurant"
                ),
                InlineKeyboardButton("🔍 Все типы", callback_data="search_type:all"),
            ],
        ]
    )


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения действий"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data="confirm:yes"),
                InlineKeyboardButton("❌ Отменить", callback_data="confirm:no"),
            ]
        ]
    )


def get_location_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса геолокации"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Отправить местоположение", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("↩️ Назад в меню", callback_data="back_to_menu")]]
    )
