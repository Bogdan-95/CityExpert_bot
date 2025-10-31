# import httpx
# from pydantic import BaseModel
# from typing import List, Optional, Dict, Tuple
# from datetime import datetime, timedelta
# from cachetools import TTLCache
# import hashlib
# from city_expert.utils.logger import logger
# from typing import Any
#
#
# class Place(BaseModel):
#     """Модель данных для представления места/достопримечательности."""
#     name: str
#     address: str
#     latitude: float
#     longitude: float
#     rating: Optional[float] = None
#     photos: List[str] = []
#     website: Optional[str] = None
#     phone: Optional[str] = None
#     opening_hours: Optional[Dict] = None
#
#
# class PlacesAPI:
#     """Класс для работы с API поиска мест."""
#
#     def __init__(self, api_key: str):
#         """
#         Args:
#             api_key: Ключ для доступа к API
#         """
#         self._api_key = api_key
#         self._base_url = "https://google-map-places-new-v2.p.rapidapi.com/v1/places:searchText"
#         self._headers = {
#             "X-RapidAPI-Key": self._api_key,
#             "X-RapidAPI-Host": "google-map-places-new-v2.p.rapidapi.com",
#             "Content-Type": "application/json",
#             "X-Goog-FieldMask": "displayName,formattedAddress,location,rating,photos,websiteUri,nationalPhoneNumber,currentOpeningHours",
#         }
#         self._search_cache = TTLCache(maxsize=100, ttl=3600)
#         self._rate_limits: Dict[int, Tuple[datetime, int]] = {}
#
#     async def __aenter__(self):
#         self._client = httpx.AsyncClient()
#         return self
#
#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         if self._client:
#             await self._client.aclose()
#
#     @staticmethod
#     def _generate_cache_key(query: str, lat: Optional[float], lon: Optional[float]) -> str:
#         """Генерирует ключ кэша на основе параметров поиска."""
#         key_data = f"{query}:{lat}:{lon}"
#         return hashlib.md5(key_data.encode()).hexdigest()
#
#     def _check_rate_limit(self, user_id: int) -> bool:
#         """Проверяет лимит запросов (5 в минуту)."""
#         now = datetime.now()
#         last_time, count = self._rate_limits.get(user_id, (now, 0))
#
#         if (now - last_time) < timedelta(minutes=1):
#             if count >= 5:
#                 return False
#             self._rate_limits[user_id] = (last_time, count + 1)
#         else:
#             self._rate_limits[user_id] = (now, 1)
#         return True
#
#     async def search(
#             self,
#             query: str,
#             latitude: Optional[float] = None,
#             longitude: Optional[float] = None,
#             radius: float = 1000.0,
#             user_id: Optional[int] = None,
#     ) -> List[Place]:
#         """
#         Поиск мест по текстовому запросу.
#         """
#         logger.debug(f"Начало поиска: '{query}' | user_id={user_id} | координаты=({latitude},{longitude})")
#
#         # Проверка лимита запросов
#         if user_id and not self._check_rate_limit(user_id):
#             logger.warning(f"Превышен лимит запросов для пользователя {user_id}")
#             raise ValueError("Превышен лимит запросов. Подождите минуту.")
#
#         # Проверка кэша
#         cache_key = self._generate_cache_key(query, latitude, longitude)
#         if cache_key in self._search_cache:
#             logger.info(f"Используются кэшированные результаты для запроса: '{query}'")
#             return self._search_cache[cache_key]
#
#         # Формирование тела запроса
#         payload = {
#             "textQuery": query,
#             "languageCode": "ru",
#             "regionCode": "RU",
#         }
#
#         # Добавление геолокации, если указана
#         if latitude and longitude:
#             payload["locationBias"] = {
#                 "circle": {
#                     "center": {"latitude": latitude, "longitude": longitude},
#                     "radius": radius,
#                 }
#             }
#
#         try:
#             # Отправка запроса
#             logger.debug(f"Отправка запроса к API для: '{query}'")
#             async with httpx.AsyncClient(timeout=15.0) as client:
#                 response = await client.post(
#                     self._base_url,
#                     headers=self._headers,
#                     json=payload,
#                 )
#
#                 if response.status_code != 200:
#                     logger.error(f"Ошибка API: статус {response.status_code}, ответ: {response.text[:200]}...")
#                     return []
#
#                 data = response.json()
#
#                 if "error" in data:
#                     logger.error(f"Ошибка в ответе API: {data['error']}")
#                     return []
#
#                 # Парсинг результатов
#                 results = []
#                 for place_data in data.get("places", []):
#                     try:
#                         place = Place(
#                             name=place_data.get("displayName", {}).get("text", "Без названия"),
#                             address=place_data.get("formattedAddress", "Адрес не указан"),
#                             latitude=place_data.get("location", {}).get("latitude", 0.0),
#                             longitude=place_data.get("location", {}).get("longitude", 0.0),
#                             rating=place_data.get("rating"),
#                             website=place_data.get("websiteUri"),
#                             phone=place_data.get("nationalPhoneNumber"),
#                             opening_hours=place_data.get("currentOpeningHours"),
#                             photos=[photo["name"] for photo in place_data.get("photos", []) if "name" in photo],
#                         )
#                         results.append(place)
#                     except Exception as e:
#                         logger.warning(f"Ошибка парсинга места: {e}", exc_info=True)
#                         continue
#
#                 # Кэширование результатов
#                 self._search_cache[cache_key] = results
#                 logger.success(f"Успешный поиск: найдено {len(results)} мест для '{query}'")
#                 return results
#
#         except Exception as e:
#             logger.error(f"Ошибка при поиске: {e}", exc_info=True)
#             return []
#
#     async def close(self):
#         """Закрытие соединения."""
#         if hasattr(self, '_client') and self._client:
#             await self._client.aclose()
#
#
#
#
#
# payload = {
#     "textQuery": query,
#     "languageCode": "ru",
#     "regionCode": "RU",
#     "locationBias": {
#         "circle": {
#             "center": {
#                 "latitude": latitude if latitude else 0,
#                 "longitude": longitude if longitude else 0
#             },
#             "radius": radius
#         }
#     }
# }
#
#
#
#
#
#
#
# #
# # import httpx
# # from pydantic import BaseModel
# # from typing import List, Optional, Dict, Tuple
# # from datetime import datetime, timedelta
# # from cachetools import TTLCache
# # import hashlib
# # from city_expert.utils.logger import logger
# # from typing import Any
# #
# #
# # class Place(BaseModel):
# #     """Модель данных для представления места/достопримечательности."""
# #     name: str
# #     address: str
# #     latitude: float
# #     longitude: float
# #     rating: Optional[float] = None
# #     photos: List[str] = []
# #     website: Optional[str] = None
# #     phone: Optional[str] = None
# #     opening_hours: Optional[Dict] = None
# #
# #
# # class PlacesAPI:
# #     """Класс для работы с API поиска мест."""
# #
# #     def __init__(self, api_key: str):
# #         """
# #         Args:
# #             api_key: Ключ для доступа к API
# #         """
# #         self._api_key = api_key
# #         self._base_url = "https://google-map-places-new-v2.p.rapidapi.com/v1/places:searchText"
# #         self._headers = {
# #             "X-RapidAPI-Key": self._api_key,
# #             "X-RapidAPI-Host": "google-map-places-new-v2.p.rapidapi.com",
# #             "Content-Type": "application/json",
# #         }
# #         self._search_cache = TTLCache(maxsize=100, ttl=3600)  # 1 час кэширования
# #         self._rate_limits: Dict[int, Tuple[datetime, int]] = {}
# #
# #     async def __aenter__(self):
# #         self._client = httpx.AsyncClient()
# #         return self
# #
# #     async def __aexit__(self, exc_type, exc_val, exc_tb):
# #         if self._client:
# #             await self._client.aclose()
# #
# #     @staticmethod
# #     def _generate_cache_key(query: str, lat: Optional[float], lon: Optional[float]) -> str:
# #         """Генерирует ключ кэша на основе параметров поиска."""
# #         key_data = f"{query}:{lat}:{lon}"
# #         return hashlib.md5(key_data.encode()).hexdigest()
# #
# #     def _check_rate_limit(self, user_id: int) -> bool:
# #         """Проверяет лимит запросов (5 в минуту)."""
# #         now = datetime.now()
# #         last_time, count = self._rate_limits.get(user_id, (now, 0))
# #
# #         if (now - last_time) < timedelta(minutes=1):
# #             if count >= 5:
# #                 return False
# #             self._rate_limits[user_id] = (last_time, count + 1)
# #         else:
# #             self._rate_limits[user_id] = (now, 1)
# #         return True
# #
# #     async def search(
# #             self,
# #             query: str,
# #             latitude: Optional[float] = None,
# #             longitude: Optional[float] = None,
# #             radius: float = 1000.0,
# #             user_id: Optional[int] = None,
# #     ) -> List[Place]:
# #         """
# #         Поиск мест по текстовому запросу с кэшированием и ограничением запросов.
# #
# #         Логирует ключевые этапы работы и ошибки для последующего анализа.
# #
# #         Args:
# #             query: Текст для поиска (например, "кафе")
# #             latitude: Широта для поиска поблизости (опционально)
# #             longitude: Долгота для поиска поблизости (опционально)
# #             radius: Радиус поиска в метрах (по умолчанию 1000м)
# #             user_id: ID пользователя для контроля лимитов запросов
# #
# #         Returns:
# #             List[Place]: Список найденных мест или пустой список при ошибке
# #
# #         Raises:
# #             ValueError: При превышении лимита запросов пользователем
# #         """
# #         # Логирование начала поиска
# #         logger.debug(f"Начало поиска: '{query}' | user_id={user_id} | координаты=({latitude},{longitude})")
# #
# #         # 1. Проверка лимита запросов
# #         if user_id and not self._check_rate_limit(user_id):
# #             logger.warning(f"Превышен лимит запросов для пользователя {user_id}")
# #             raise ValueError("Превышен лимит запросов. Подождите минуту.")
# #
# #         # 2. Проверка кэша
# #         cache_key = self._generate_cache_key(query, latitude, longitude)
# #         if cache_key in self._search_cache:
# #             logger.info(f"Используются кэшированные результаты для запроса: '{query}'")
# #             return self._search_cache[cache_key]
# #
# #         # 3. Формирование запроса
# #         payload = {
# #             "fieldMask": "displayName,"
# #             "formattedAddress,location,rating,photos,"
# #             "websiteUri,nationalPhoneNumber,currentOpeningHours",
# #             "textQuery": query,
# #             "languageCode": "ru",  # Язык результатов - русский
# #             "regionCode": "RU",  # Регион поиска - Россия
# #
# #         }
# #
# #         # Добавление геолокации в запрос, если указаны координаты
# #         if latitude and longitude:
# #             payload: Dict[str, Any] = {
# #             "locationBias": {
# #                 "circle": {
# #                     "center": {"latitude": latitude, "longitude": longitude},
# #                     "radius": radius,
# #                 }
# #             }
# #         }
# #             logger.debug(f"Поиск с геолокацией: радиус {radius}м")
# #
# #         try:
# #             # 4. Выполнение HTTP-запроса к API
# #             logger.debug(f"Отправка запроса к API для: '{query}'")
# #             async with httpx.AsyncClient(timeout=15.0) as client:
# #                 response = await client.post(
# #                     self._base_url,
# #                     headers=self._headers,
# #                     json=payload,
# #                 )
# #
# #                 # Обработка ошибок HTTP
# #                 if response.status_code != 200:
# #                     logger.error(f"Ошибка API: статус {response.status_code}, ответ: {response.text[:200]}...")
# #                     return []
# #
# #                 data = response.json()
# #
# #                 # Обработка ошибок API
# #                 if "error" in data:
# #                     logger.error(f"Ошибка в ответе API: {data['error']}")
# #                     return []
# #
# #                 # 5. Парсинг результатов
# #                 results = []
# #                 logger.debug(f"Начало обработки {len(data.get('places', []))} результатов")
# #
# #                 for place_data in data.get("places", []):
# #                     try:
# #                         # Извлечение фото (безопасная обработка)
# #                         photos = [
# #                             photo["name"]
# #                             for photo in place_data.get("photos", [])
# #                             if "name" in photo
# #                         ]
# #
# #                         # Создание объекта Place
# #                         place = Place(
# #                             name=place_data.get("displayName", {}).get("text", "Без названия"),
# #                             address=place_data.get("formattedAddress", "Адрес не указан"),
# #                             latitude=place_data.get("location", {}).get("latitude", 0.0),
# #                             longitude=place_data.get("location", {}).get("longitude", 0.0),
# #                             rating=place_data.get("rating"),
# #                             website=place_data.get("websiteUri"),
# #                             phone=place_data.get("nationalPhoneNumber"),
# #                             opening_hours=place_data.get("currentOpeningHours"),
# #                             photos=photos,
# #                         )
# #                         results.append(place)
# #                     except Exception as e:
# #                         logger.warning(f"Ошибка парсинга места: {e}", exc_info=True)
# #                         continue
# #
# #                 # 6. Кэширование результатов
# #                 self._search_cache[cache_key] = results
# #                 logger.success(f"Успешный поиск: найдено {len(results)} мест для '{query}'")
# #                 return results
# #
# #         except httpx.ConnectError:
# #             logger.error("Ошибка подключения к API: проверьте интернет-соединение")
# #             return []
# #         except httpx.TimeoutException:
# #             logger.warning("Таймаут запроса к API: превышено время ожидания")
# #             return []
# #         except Exception as e:
# #             logger.error(f"Неожиданная ошибка при поиске: {e}", exc_info=True)
# #             return []
# #         except (httpx.HTTPError, ValueError, KeyError) as e:
# #             logger.error(f"Ошибка при обработке: {e}")
# #             return []
# #
# #     async def close(self):
# #         """Закрытие соединения."""
# #         if hasattr(self, '_client') and self._client:
# #             await self._client.aclose()
# #
