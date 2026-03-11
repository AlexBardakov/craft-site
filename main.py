import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from routers import client, admin, order, customer

import models
from database import engine

# Импортируем наши роутеры из папки routers
from routers import client, admin, order

load_dotenv()

# Создаем таблицы в базе (если их еще нет)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Сайт Бюро Кошачье")

# Подключаем папку со статикой (картинки, стили)
app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs("static/images", exist_ok=True)

# ПОДКЛЮЧАЕМ МАРШРУТЫ ИЗ ФАЙЛОВ
app.include_router(client.router)
app.include_router(admin.router)
app.include_router(order.router)
app.include_router(customer.router)

