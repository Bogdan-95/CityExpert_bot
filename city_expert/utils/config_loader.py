from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
from typing import Final, Literal

# Определяем путь к .env файлу (3 уровня выше текущего файла)
ENV_PATH: Final[Path] = Path(__file__).parent.parent.parent / ".env"

# Загружаем переменные окружения из файла
load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    """
    Класс конфигурации приложения, наследующийся от BaseSettings.
    Все параметры автоматически загружаются из переменных окружения.
    Attributes:
        TELEGRAM_BOT_TOKEN (str): Токен бота Telegram (обязательный)
        RAPIDAPI_KEY (str): Ключ для доступа к RapidAPI (обязательный)
        DATABASE_URL (str): URL подключения к БД (по умолчанию SQLite)
        DEBUG (bool): Режим отладки (по умолчанию False)
        LOG_LEVEL (str): Уровень логирования (по умолчанию INFO)
    """

    # Обязательные параметры (без значений по умолчанию)
    TELEGRAM_BOT_TOKEN: str
    RAPIDAPI_KEY: str

    DATABASE_URL: str = "sqlite:///data/city_expert.db"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


    class Config:
        """
        Вложенный класс конфигурации для настроек Pydantic.
         Attributes:
            env_file (str): Путь к .env файлу
            env_file_encoding (str): Кодировка файла (по умолчанию utf-8)
            extra (str): Поведение при лишних переменных (ignore - игнорировать)
        """
        env_file: str = ENV_PATH
        env_file_encoding: str = "utf-8"
        extra: str = "ignore"


class APIConfig:
    """
    Класс для хранения всех конфигураций API.

    Attributes:
        BASE_URL (str): Базовый URL API (без протокола)
        SEARCH_TEXT_ENDPOINT (str): Эндпоинт для текстового поиска
        NEARBY_SEARCH_ENDPOINT (str): Эндпоинт для поиска поблизости
        PLACE_DETAILS_ENDPOINT (str): Эндпоинт для деталей места
        DEFAULT_HEADERS (dict): Заголовки по умолчанию для API запросов
        DEFAULT_RADIUS (float): Радиус поиска по умолчанию (в метрах)
        RATE_LIMIT (dict): Настройки ограничения запросов
    """
    BASE_URL: Final[str] = "google-map-places-new-v2.p.rapidapi.com"
    SEARCH_TEXT_ENDPOINT: Final[str] = "/v1/places:searchText"
    NEARBY_SEARCH_ENDPOINT: Final[str] = "/v1/places:searchNearby"
    PLACE_DETAILS_ENDPOINT: Final[str] = "/v1/places:getDetails"

    DEFAULT_RADIUS: Final[float] = 1000.0  # 1 км

    RATE_LIMIT: Final[dict] = {
        "requests": 5,
        "period": 60  # секунд
    }

    @classmethod
    def get_headers(cls, api_key: str) -> dict:
        """
        Возвращает заголовки для API запросов.

        Args:
            api_key: Ключ API для авторизации

        Returns:
            dict: Заголовки запроса
        """
        return {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": cls.BASE_URL,
            "Content-Type": "application/json",
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,"
                                "places.websiteUri,places.nationalPhoneNumber,places.currentOpeningHours,"
                                "places.photos"
        }



def load_config() -> Settings:
    """
    Функция для загрузки и валидации конфигурации приложения.

    Returns:
        Settings: Экземпляр класса настроек с загруженными значениями

    Raises:
        ValidationError: Если обязательные параметры не указаны или невалидны
    """
    return Settings()


# Инициализация конфигурации
config: Settings = load_config()
api_config = APIConfig()