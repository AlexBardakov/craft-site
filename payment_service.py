import uuid


# ВРЕМЕННАЯ ЗАГЛУШКА (MOCK) ДЛЯ ТЕСТИРОВАНИЯ БЕЗ API ЮKASSA
# Когда дадут доступ, мы просто вернем сюда старый код с импортом yookassa

def create_sbp_payment(order_id: int, amount: int, description: str):
    """
    Имитирует ответ от ЮKassa: генерирует случайный ID и фейковую ссылку.
    """
    # 1. Генерируем случайный набор символов в качестве ID "платежа"
    fake_payment_id = str(uuid.uuid4())

    # 2. Формируем безопасную фейковую ссылку (она просто откроет страницу-заглушку example.com)
    fake_confirmation_url = f"https://example.com/yookassa-mock-pay?order={order_id}&sum={amount}"

    # Печатаем в консоль сервера, чтобы ты видел, что функция отработала
    print(
        f"✅ [MOCK ЮKassa] Выставлен счет для заказа #{order_id} на сумму {amount} руб.")
    print(f"🔗 Ссылка: {fake_confirmation_url}")

    return fake_payment_id, fake_confirmation_url