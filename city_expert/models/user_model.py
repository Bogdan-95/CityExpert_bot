
from peewee import BigIntegerField, CharField, DateTimeField, ForeignKeyField
from datetime import datetime
from .base_model import BaseModel

class User(BaseModel):
    """
    Модель пользователя Telegram бота.

    Хранит основную информацию о пользователях, взаимодействующих с ботом.
    """
    telegram_id = BigIntegerField(unique=True)  # Уникальный идентификатор пользователя в Telegram
    full_name = CharField()  # Полное имя пользователя
    username = CharField(null=True)  # Имя пользователя
    created_at = DateTimeField(default=datetime.now)  # Дата и время регистрации пользователя

    class Meta:
        table_name = "users"  # Название таблицы в базе данных


class FavoritePlace(BaseModel):
    """
    Модель для хранения избранных мест пользователя.

    Связана с моделью User через внешний ключ и позволяет хранить
    информацию о местах, которые пользователь добавил в избранное.
    """
    user = ForeignKeyField(User, backref="favorites", on_delete="CASCADE")  # Связь с пользователем (при удалении пользователя удаляются и его избранные места)
    place_id = CharField(max_length=128)  # Идентификатор места (обычно координаты или внешний ID)
    name = CharField(max_length=256)  # Название места
    added_at = DateTimeField(default=datetime.now)  # Дата и время добавления в избранное

    class Meta:
        table_name = "favorite_places"  # Название таблицы в базе данных
        indexes = (
            (("user", "place_id"), True),  # Создание уникального составного индекса для пары (пользователь, место)
        )
