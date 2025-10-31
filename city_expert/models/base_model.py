from peewee import Model  # Импортируем базовый класс модели из peewee ORM
from .database import db_proxy  # Импортируем прокси-объект базы данных из локального модуля database


class BaseModel(Model):
    """
    Базовая модель для всех ORM-моделей проекта.
    Все модели должны наследоваться от BaseModel, чтобы использовать общий прокси-объект базы данных.
    """
    class Meta:
        database = db_proxy  # Указываем, что все дочерние модели будут использовать db_proxy как подключение к БД


