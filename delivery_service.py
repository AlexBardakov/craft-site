import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Тестовые ключи СДЭК (Песочница). Потом заменишь на боевые и уберешь .edu из URL
CDEK_CLIENT_ID = os.getenv("CDEK_CLIENT_ID",
                           "z9GRR7S1V2A5sTqZ5Q7Vz1r6G9S3p0i7")
CDEK_CLIENT_SECRET = os.getenv("CDEK_CLIENT_SECRET",
                               "u9Z9Q3R1V2A5sTqZ5Q7Vz1r6G9S3p0i7")
CDEK_AUTH_URL = "https://api.edu.cdek.ru/v2/oauth/token"
CDEK_CITY_URL = "https://api.edu.cdek.ru/v2/location/cities"
CDEK_CALC_URL = "https://api.edu.cdek.ru/v2/calculator/tariff"


async def get_cdek_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(CDEK_AUTH_URL, data={
            "grant_type": "client_credentials",
            "client_id": CDEK_CLIENT_ID,
            "client_secret": CDEK_CLIENT_SECRET
        })
        if response.status_code == 200:
            return response.json().get("access_token")
    return None


async def calculate_delivery_cost(city_name: str, method: str) -> int:
    """
    Получает город текстом и возвращает стоимость доставки в рублях.
    """
    if not city_name:
        return 0

    if method == "СДЭК":
        token = await get_cdek_token()
        if not token:
            return 500  # Запасной тариф при ошибке API

        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            # 1. Ищем код города по названию
            city_resp = await client.get(f"{CDEK_CITY_URL}?city={city_name}",
                                         headers=headers)
            cities = city_resp.json()
            if not cities:
                return 500
            city_code = cities[0].get("code")

            # 2. Считаем тариф (тариф 136 - посылка до ПВЗ). Вес ставим условно 300 грамм
            calc_resp = await client.post(CDEK_CALC_URL, headers=headers,
                                          json={
                                              "tariff_code": 136,
                                              "to_location": {
                                                  "code": city_code},
                                              "packages": [
                                                  {"weight": 300, "length": 15,
                                                   "width": 10, "height": 10}]
                                          })

            if calc_resp.status_code == 200:
                calc_data = calc_resp.json()
                return int(calc_data.get("delivery_sum", 500))

        return 500  # Если расчет не удался

    elif method == "Почта России":
        # Для Почты России API сложнее (требует индекс),
        # поэтому пока оставляем заглушку, которую потом тоже заменим на API.
        # Но чтобы было реалистично: чем длиннее название города, тем "дальше" :)
        return 350 if len(city_name) < 10 else 450

    return 0