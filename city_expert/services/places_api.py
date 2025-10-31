import httpx
from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime, timedelta
from cachetools import TTLCache
import hashlib
from city_expert.utils.logger import logger
from city_expert.utils.config_loader import api_config


class Place(BaseModel):
    """Модель данных для представления места/достопримечательности."""
    name: str
    address: str
    latitude: float
    longitude: float
    rating: Optional[float] = None
    photos: List[str] = []
    website: Optional[str] = None
    phone: Optional[str] = None
    opening_hours: Optional[Dict[str, Any]] = None


class PlacesAPI:
    """Класс для работы с API поиска мест."""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Ключ для доступа к API
        """
        self._api_key = api_key
        self._search_cache: TTLCache = TTLCache(maxsize=100, ttl=3600)
        self._rate_limits: Dict[int, Tuple[datetime, int]] = {}
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "PlacesAPI":
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @staticmethod
    def _generate_cache_key(query: str, lat: Optional[float], lon: Optional[float]) -> str:
        """Генерирует ключ кэша на основе параметров поиска."""
        key_data = f"{query}:{lat}:{lon}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _check_rate_limit(self, user_id: int) -> bool:
        """Проверяет лимит запросов (5 в минуту)."""
        now = datetime.now()
        last_time, count = self._rate_limits.get(user_id, (now, 0))

        if (now - last_time) < timedelta(minutes=1):
            if count >= api_config.RATE_LIMIT["requests"]:
                return False
            self._rate_limits[user_id] = (last_time, count + 1)
        else:
            self._rate_limits[user_id] = (now, 1)
        return True

    async def search(
            self,
            query: str,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            radius: float = api_config.DEFAULT_RADIUS,
            user_id: Optional[int] = None,
    ) -> List[Place]:
        if latitude is None or longitude is None:
            logger.warning("Геолокация не указана! Поиск будет по общему региону.")

        # Проверка лимита запросов
        if user_id and not self._check_rate_limit(user_id):
            logger.warning(f"Превышен лимит запросов для пользователя {user_id}")
            raise ValueError("Превышен лимит запросов. Подождите минуту.")

        # Проверка кэша
        cache_key = self._generate_cache_key(query, latitude, longitude)
        if cache_key in self._search_cache:
            cached_results = self._search_cache[cache_key]
            if isinstance(cached_results, list):
                logger.info(f"Используются кэшированные результаты для запроса: '{query}'")
                return cached_results
            return []

        # Формирование тела запроса для searchNearby
        payload = {
            "languageCode": "ru",
            "regionCode": "RU",
            "maxResultCount": 20,  # Ограничиваем количество результатов
            "rankPreference": "DISTANCE"  # Сортировка по расстоянию
        }

        # Если есть текст запроса, используем includedTypes
        if query:
            # Преобразуем общий запрос в конкретные типы мест
            place_types = self._map_query_to_types(query)
            if place_types:
                payload["includedTypes"] = place_types
            else:
                # Если не удалось сопоставить с типами, используем текстовый поиск через searchText
                return await self._search_by_text(query, latitude, longitude, radius, user_id)

        if latitude is not None and longitude is not None:
            payload["locationRestriction"] = {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": radius
                }
            }

        headers = api_config.get_headers(self._api_key)

        try:
            logger.debug(f"Отправка запроса к API для: '{query}'")
            if not self._client:
                self._client = httpx.AsyncClient()

            url = f"https://{api_config.BASE_URL}{api_config.NEARBY_SEARCH_ENDPOINT}"
            logger.debug(f"URL запроса: {url}")

            response = await self._client.post(
                url,
                headers=headers,
                json=payload,
                timeout=15.0
            )

            if response.status_code != 200:
                logger.error(f"Ошибка API: статус {response.status_code}, ответ: {response.text[:200]}...")
                return []

            data = response.json()
            if "error" in data:
                logger.error(f"Ошибка в ответе API: {data['error']}")
                return []

            results: List[Place] = []
            for place_data in data.get("places", []):
                try:
                    place = self._parse_place_data(place_data)
                    if place:
                        results.append(place)
                except Exception as e:
                    logger.warning(f"Ошибка парсинга места: {e}", exc_info=True)
                    continue

            self._search_cache[cache_key] = results
            logger.success(f"Успешный поиск: найдено {len(results)} мест для '{query}'")
            return results

        except httpx.RequestError as e:
            logger.error(f"Ошибка сети при поиске: {e}")
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка при поиске: {e}", exc_info=True)
            return []

    async def _search_by_text(
            self,
            query: str,
            latitude: Optional[float],
            longitude: Optional[float],
            radius: float,
            user_id: Optional[int]
    ) -> List[Place]:
        """Альтернативный поиск через searchText endpoint."""
        payload = {
            "textQuery": query,
            "languageCode": "ru",
            "regionCode": "RU",
            "maxResultCount": 20
        }

        if latitude is not None and longitude is not None:
            payload["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": radius
                }
            }

        headers = api_config.get_headers(self._api_key)

        try:
            if not self._client:
                self._client = httpx.AsyncClient()

            url = f"https://{api_config.BASE_URL}{api_config.SEARCH_TEXT_ENDPOINT}"
            logger.debug(f"Альтернативный текстовый поиск: {url}")

            response = await self._client.post(
                url,
                headers=headers,
                json=payload,
                timeout=15.0
            )

            if response.status_code != 200:
                logger.error(f"Ошибка текстового поиска: статус {response.status_code}")
                return []

            data = response.json()
            results: List[Place] = []
            for place_data in data.get("places", []):
                try:
                    place = self._parse_place_data(place_data)
                    if place:
                        results.append(place)
                except Exception as e:
                    logger.warning(f"Ошибка парсинга места в текстовом поиске: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Ошибка текстового поиска: {e}")
            return []

    def _map_query_to_types(self, query: str) -> List[str]:
        """Преобразует текстовый запрос в типы мест Google Places."""
        query_lower = query.lower()
        type_mapping = {
            'ресторан': 'restaurant',
            'кафе': 'cafe',
            'бар': 'bar',
            'кофейня': 'cafe',
            'магазин': 'store',
            'аптека': 'pharmacy',
            'банк': 'bank',
            'больница': 'hospital',
            'отель': 'hotel',
            'кинотеатр': 'movie_theater',
            'парк': 'park',
            'музей': 'museum',
            'театр': 'performing_arts_theater'
        }

        for rus_type, eng_type in type_mapping.items():
            if rus_type in query_lower:
                return [eng_type]

        return []

    def _parse_place_data(self, place_data: dict) -> Optional[Place]:
        """Парсит данные места из ответа API."""
        try:
            opening_hours = place_data.get("currentOpeningHours", {})
            place = Place(
                name=place_data.get("displayName", {}).get("text", "Без названия"),
                address=place_data.get("formattedAddress", "Адрес не указан"),
                latitude=place_data.get("location", {}).get("latitude", 0.0),
                longitude=place_data.get("location", {}).get("longitude", 0.0),
                rating=place_data.get("rating"),
                website=place_data.get("websiteUri"),
                phone=place_data.get("nationalPhoneNumber"),
                opening_hours={
                    "open_now": opening_hours.get("openNow", False),
                    "periods": opening_hours.get("periods", [])
                } if opening_hours else None,
                photos=[photo["name"] for photo in place_data.get("photos", []) if "name" in photo],
            )
            return place
        except Exception as e:
            logger.warning(f"Ошибка создания объекта Place: {e}")
            return None

    async def close(self) -> None:
        """Закрытие соединения."""
        if self._client:
            await self._client.aclose()
            self._client = None