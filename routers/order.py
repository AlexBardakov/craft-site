import os
from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

import models
from database import get_db

router = APIRouter()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")


@router.post("/order")
async def process_order(
        product_id: int = Form(...),
        contact: str = Form(...),
        db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id).first()

    if product and BOT_TOKEN and ADMIN_CHAT_ID:
        message_text = (
            f"🚀 <b>НОВЫЙ ЗАКАЗ С САЙТА!</b>\n\n"
            f"📦 <b>Товар:</b> {product.title}\n"
            f"🏷 <b>Категория:</b> {product.category}\n"
            f"💰 <b>Цена:</b> {product.price} ₽\n"
            f"👤 <b>Контакт:</b> {contact}\n\n"
            f"Свяжитесь с ним для уточнения деталей доставки."
        )

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