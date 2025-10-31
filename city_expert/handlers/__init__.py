# Импорт функции настройки обработчиков из модуля user_controller текущего пакета


from .user_controller import setup_handlers

__all__ = ["setup_handlers"]
