
from city_expert.models import (
    db_proxy,
    init_db,
    User,
    FavoritePlace,
    SearchModel,
)


def create_tables():
    db_path = r"D:\pyCharm\python_basic_diploma\city_expert\data\city_expert.db"
    init_db(db_path)

    with db_proxy:
        User.create_table(safe=True)
        FavoritePlace.create_table(safe=True)
        SearchModel.create_table(safe=True)  # Создаем таблицу для SearchModel
        print("Таблицы User, FavoritePlace и SearchModel созданы/проверены")


if __name__ == "__main__":
    create_tables()
