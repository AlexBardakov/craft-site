import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# Настройки SMTP (добавишь в .env перед выходом в продакшн)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "") # Здесь нужен "пароль приложения" от почты

def send_reset_email(to_email: str, reset_link: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        # Если почта не настроена, просто выводим ссылку в консоль (для тестов)
        print(f"\n📧 [MOCK EMAIL] Письмо для {to_email}")
        print(f"🔗 Ссылка для сброса пароля: {reset_link}\n")
        return

    msg = EmailMessage()
    msg.set_content(f"Здравствуйте!\n\nВы запросили сброс пароля на сайте Бюро Кошачье.\nДля установки нового пароля перейдите по ссылке (она действительна 15 минут):\n\n{reset_link}\n\nЕсли вы не делали этот запрос, просто проигнорируйте письмо.")
    msg['Subject'] = "Восстановление пароля | Бюро Кошачье"
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")