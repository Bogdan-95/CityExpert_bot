from telegram.helpers import escape_markdown
from city_expert.models import SearchModel
from city_expert.services.places_api import Place
from typing import List


def format_search_results(results: List[Place]) -> str:
    """
    Форматирует список найденных мест в читаемое сообщение Markdown.

    Args:
        results: Список объектов Place с результатами поиска

    Returns:
        Отформатированная строка с результатами или сообщение об отсутствии результатов

    Формат вывода:
        🔍 Результаты поиска:
        🏛 Название места
        📍 Адрес
        ⭐ Рейтинг
        🌐 Координаты: широта, долгота
        ━━━━━━━━━━━━━━
    """
    if not results:
        return "Ничего не найдено 😕\nПопробуйте изменить запрос"

    formatted = ["🔍 *Результаты поиска:*\n"]  # Заголовок с Markdown-разметкой

    for place in results[:5]:  # Ограничиваем 5 результатами
        # Экранирование специальных символов для MarkdownV2
        name = escape_markdown(place.name, version=2)
        address = escape_markdown(place.address, version=2)

        # Форматирование рейтинга (если есть)
        rating = f"⭐ {place.rating:.1f}" if place.rating else "⭐ нет оценок"

        # Формирование блока информации о месте
        formatted.append(
            f"🏛 *{name}*\n"  # Жирный шрифт для названия
            f"📍 {address}\n"
            f"{rating}\n"
            f"🌐 Координаты: {place.latitude:.6f}, {place.longitude:.6f}\n"
            "━━━━━━━━━━━━━━"  # Разделитель
        )

    return "\n".join(formatted)


def format_history(history: List[SearchModel]) -> str:
    """
    Форматирует историю поисковых запросов в читаемое сообщение Markdown.

    Args:
        history: Список объектов SearchModel с историей запросов

    Returns:
        Отформатированная строка с историей или сообщение об её отсутствии

    Формат вывода:
        📆 История запросов:
        1. Поисковый запрос
           🕒 Дата | 📍 Координаты | 🏙 Найдено: количество
           ━━━━━━━━━━━━━━
    """
    if not history:
        return "📭 История запросов пуста"

    formatted = ["📆 *История запросов:*\n"]  # Заголовок с Markdown-разметкой

    for idx, record in enumerate(history, 1):
        # Форматирование даты и времени
        date = record.created_at.strftime("%d.%m.%Y %H:%M")

        # Получение количества результатов (если есть)
        results = record.results_count()
        count = len(results) if results else 0

        # Добавление координат (если есть)
        location = ""
        if record.latitude and record.longitude:
            location = f" | 📍 {record.latitude:.4f}, {record.longitude:.4f}"

        # Формирование строки с информацией о запросе
        formatted.append(
            f"{idx}. *{escape_markdown(record.query, version=2)}*\n"  # Жирный запрос
            f"   🕒 {date}{location} | 🏙 Найдено: {count}\n"
            "   ━━━━━━━━━━━━━━"  # Разделитель с отступом
        )

    return "\n".join(formatted)  # Объединяем все строки