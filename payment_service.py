import os
import uuid
from yookassa import Configuration, Payment
from dotenv import load_dotenv

load_dotenv()

# Инициализация API ЮKassa
Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")


def create_sbp_payment(order_id: int, amount: int, description: str):
    """
    Создает платеж строго через СБП и возвращает (payment_id, confirmation_url)
    """
    # Уникальный ключ идемпотентности нужен для защиты от двойного списания
    # при обрыве связи во время запроса
    idempotence_key = str(uuid.uuid4())

    payment = Payment.create({
        "amount": {
            "value": f"{amount}.00",
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "sbp"
            # Форсируем оплату именно через Систему быстрых платежей
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/твой_контакт"
            # Куда вернуть клиента после оплаты. Пока можно указать твой ТГ
        },
        "capture": True,  # Автоматический холд и списание
        "description": description,
        "metadata": {
            "order_id": order_id
            # Сохраняем ID заказа Сайт Сыроварни для связки при получении Webhook
        }
    }, idempotence_key)

    return payment.id, payment.confirmation.confirmation_url