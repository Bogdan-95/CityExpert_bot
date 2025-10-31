from .database import db_proxy, init_db

# Импортируем базовую модель для наследования ORM-моделей
from .base_model import BaseModel

# Импортируем модели пользователя и избранных мест
from .user_model import User, FavoritePlace

# Импортируем модель истории поиска
from .search_model import SearchModel

# Определяем публичный API пакета:
# При импорте через from <package> import * будут доступны только перечисленные ниже объекты
__all__ = [
    "db_proxy",        # Прокси-объект базы данных для Peewee
    "init_db",         # Функция инициализации базы данных
    "BaseModel",       # Базовая модель для всех ORM-моделей
    "User",            # Модель пользователя
    "FavoritePlace",   # Модель избранных мест пользователя
    "SearchModel",     # Модель истории поиска
]
