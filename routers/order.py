import os
import json
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
from dotenv import load_dotenv

import models
from database import get_db

load_dotenv()

router = APIRouter()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")


@router.post("/order")
async def process_order(
        cart_data: str = Form(...),
        # Теперь принимаем строку с JSON-данными корзины
        contact: str = Form(...),
        comment: str = Form(""),  # Комментарий теперь тоже сохраняем
        db: Session = Depends(get_db)
):
    # 1. Расшифровываем JSON строку обратно в список товаров
    try:
        cart = json.loads(cart_data)
    except json.JSONDecodeError:
        cart = []

    if not cart:
        # Если корзина по какой-то причине пуста, возвращаем обратно
        return RedirectResponse(url="/cart", status_code=303)

    # 2. Считаем итоговую сумму и формируем красивый текст для чека
    items_text = ""
    total_price = 0

    for item in cart:
        title = item.get("title", "Неизвестный товар")
        price = int(item.get("price", 0))
        qty = int(item.get("quantity", 1))

        # Проверяем, на заказ ли эта позиция
        is_custom = item.get("is_custom", False)
        prefix = "🛠 [НА ЗАКАЗ]" if is_custom else "📦 [В НАЛИЧИИ]"

        item_total = price * qty
        total_price += item_total

        items_text += f"{prefix} {title} (x{qty}) - {item_total} ₽\n"

    # 3. Сохраняем заказ в НАШУ БАЗУ ДАННЫХ (в новые таблицы Order)
    new_order = models.Order(
        customer_contact=contact,
        total_price=total_price,
        comment=comment,
        status="Новый"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)  # Обновляем, чтобы получить уникальный ID заказа

    # Добавляем каждый товар из корзины в связующую таблицу OrderItem
    for item in cart:
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=int(item.get("id", 0)),
            quantity=int(item.get("quantity", 1)),
            price_at_order=int(item.get("price", 0))
        )
        db.add(order_item)
    db.commit()

    # 4. Отправляем уведомление в Telegram
    if BOT_TOKEN and ADMIN_CHAT_ID:
        message_text = (
            f"🚀 <b>НОВЫЙ ЗАКАЗ #{new_order.id} С САЙТА!</b>\n\n"
            f"📦 <b>Состав заказа:</b>\n{items_text}\n"
            f"💰 <b>Итоговая сумма:</b> {total_price} ₽\n\n"
            f"👤 <b>Контакт:</b> {contact}\n"
        )

        if comment:
            message_text += f"📝 <b>Комментарий:</b> {comment}\n"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": message_text,
            "parse_mode": "HTML"
        }

        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                print(f"Ошибка при отправке: {e}")

    return RedirectResponse(url="/success", status_code=303)


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        # Получаем JSON с данными от ЮKassa
        payload = await request.json()

        # Проверяем, что это событие успешной оплаты
        if payload.get("event") == "payment.succeeded":
            object_data = payload.get("object", {})
            metadata = object_data.get("metadata", {})

            # Достаем ID заказа, который мы передавали при выставлении счета
            order_id = metadata.get("order_id")

            if order_id:
                order = db.query(models.Order).filter(
                    models.Order.id == int(order_id)).first()
                if order and not order.is_paid:
                    # Помечаем как оплаченный
                    order.is_paid = True
                    # Автоматически двигаем статус дальше
                    if order.status in ["Новый", "Ожидает оплаты"]:
                        order.status = "В очереди"
                    db.commit()

        # ЮKassa требует всегда отвечать 200 OK, иначе она будет слать уведомления бесконечно
        return Response(status_code=200)

    except Exception as e:
        print(f"Ошибка при обработке Webhook: {e}")
        return Response(status_code=400)