from peewee import (
    Model,
    ForeignKeyField,
    CharField,
    TextField,
    FloatField,
    DateTimeField,
    BooleanField,
    IntegerField,
)
from datetime import datetime
from .database import db_proxy
from .user_model import User


class SearchModel(Model):
    """
    Модель для хранения истории поисковых запросов пользователя и их результатов.

    Атрибуты:
        user (ForeignKeyField): Ссылка на пользователя, выполнившего поиск.
        query (CharField): Исходный поисковый запрос пользователя.
        result (TextField): Текстовое представление найденных результатов (может быть пустым).
        latitude (FloatField): Широта, если поиск был по координатам.
        longitude (FloatField): Долгота, если поиск был по координатам.
        rating (FloatField): Средний рейтинг найденных мест.
        is_favorite (BooleanField): Флаг, добавлен ли результат в избранное.
        results_count (IntegerField): Количество найденных результатов.
        created_at (DateTimeField): Дата и время выполнения поиска.
    """
    user = ForeignKeyField(User, backref="searches")  # связь с пользователем
    query = CharField()                               # поисковый запрос
    result = TextField(null=True)                     # результаты поиска (JSON или текст)
    latitude = FloatField(null=True)                  # широта поиска
    longitude = FloatField(null=True)                 # долгота поиска
    rating = FloatField(null=True)                    # рейтинг
    is_favorite = BooleanField(default=False)         # признак избранного
    results_count = IntegerField(default=0)           # количество найденных результатов
    created_at = DateTimeField(default=datetime.now)  # время создания записи

    class Meta:
        database = db_proxy
        table_name = "search_history"  # имя таблицы в базе данных
