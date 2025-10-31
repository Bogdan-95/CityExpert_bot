import os

def print_project_structure(start_path, indent=''):
    print(f"{indent}📁 {os.path.basename(start_path)}")
    indent += '    '
    for item in sorted(os.listdir(start_path)):  # Сортируем файлы и папки
        item_path = os.path.join(start_path, item)
        if os.path.isdir(item_path):
            print_project_structure(item_path, indent)
        else:
            print(f"{indent}📄 {item}")

project_path = r"D:\pyCharm\python_basic_diploma\city_expert"
print_project_structure(project_path)


#
# очистка кеша


import os
import shutil
from pathlib import Path


def clean_pycache(root_path):
  root = Path(root_path)
  print(f"🧹 Очистка кеша в {root}...")

  # Удаляем все __pycache__ папки
  for pycache_dir in root.glob("**/__pycache__"):
    print(f"🗑️ Удаление {pycache_dir}")
    shutil.rmtree(pycache_dir, ignore_errors=True)

  # Удаляем все .pyc и .pyo файлы
  for pyc_file in root.glob("**/*.pyc"):
    print(f"🗑️ Удаление {pyc_file}")
    pyc_file.unlink(missing_ok=True)

  for pyo_file in root.glob("**/*.pyo"):
    print(f"🗑️ Удаление {pyo_file}")
    pyo_file.unlink(missing_ok=True)

  print("✅ Готово! Кеш очищен.")
#

# Укажите путь к проекту (можно использовать ваш путь)
project_path = r"D:\pyCharm\python_basic_diploma\city_expert"
clean_pycache(project_path)


#
#
# import pytest
# from city_expert.services.places_api import PlacesAPI
#
#
# @pytest.mark.asyncio
# async def test_api_key():
#     api_key = "2c6ab6fe4dmsh658ab187ecf5945p1020f3jsn2593eb117114"
#     async with PlacesAPI(api_key) as api:
#         # Тестируем с разными параметрами
#         test_cases = [
#             {"query": "ресторан", "lat": 55.75, "lon": 37.61},  # Москва
#             {"query": "cafe", "lat": 40.71, "lon": -74.00},  # Нью-Йорк
#             {"query": "restaurant", "lat": 48.85, "lon": 2.35}  # Париж
#         ]
#
#         for case in test_cases:
#             results = await api.search(
#                 case["query"],
#                 latitude=case["lat"],
#                 longitude=case["lon"]
#             )
#             print(f"Запрос: '{case['query']}' в ({case['lat']}, {case['lon']})")
#             print(f"Найдено мест: {len(results)}")
#             if results:
#                 for place in results[:3]:
#                     print(f"🔹 {place.name} | Адрес: {place.address}")
#             else:
#                 print("⚠️ Ничего не найдено или ошибка API")
#             print("-" * 50)