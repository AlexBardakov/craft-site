import os
import shutil
import secrets
from typing import List, Optional
from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, \
    HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import httpx

import models
from database import SessionLocal, engine

# Загружаем переменные окружения из файла .env
load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Сайт Бюро Кошачье")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

os.makedirs("static/images", exist_ok=True)

# Инициализируем базовую защиту для админки
security = HTTPBasic()

# Получаем конфиденциальные данные
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Функция проверки пароля для админки
def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_user_ok = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_pass_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# --- GET маршруты для пользователей (без пароля) ---
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request, db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return templates.TemplateResponse("index.html", {"request": request,
                                                     "products": products})


@app.get("/info", response_class=HTMLResponse)
async def read_info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})


@app.get("/success", response_class=HTMLResponse)
async def read_success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/contacts", response_class=HTMLResponse)
async def read_contacts(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
async def read_terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/product/{product_id}", response_class=HTMLResponse)
async def read_product(request: Request, product_id: int,
                       db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("product.html",
                                      {"request": request, "product": product})


# --- ЗАЩИЩЕННАЯ АДМИНКА ---
# Обрати внимание: во все функции ниже добавлен Depends(get_current_admin)

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request, db: Session = Depends(get_db),
                     admin: str = Depends(get_current_admin)):
    products = db.query(models.Product).all()
    return templates.TemplateResponse("admin.html", {"request": request,
                                                     "products": products})


@app.post("/admin/add")
async def add_product(
        title: str = Form(...),
        price: int = Form(...),
        description: str = Form(...),
        image: UploadFile = File(...),
        gallery: Optional[List[UploadFile]] = File(None),
        specifications: str = Form(""),
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    main_image_path = f"static/images/{image.filename}"
    with open(main_image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    gallery_paths = []
    if gallery:
        for file in gallery:
            if file.filename:
                g_path = f"static/images/gal_{file.filename}"
                with open(g_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                gallery_paths.append(f"/{g_path}")

    gallery_urls_str = ",".join(gallery_paths)

    new_product = models.Product(
        title=title,
        price=price,
        description=description,
        image_url=f"/{main_image_path}",
        gallery_urls=gallery_urls_str,
        specifications=specifications
    )
    db.add(new_product)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/delete/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db),
                         admin: str = Depends(get_current_admin)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/admin/edit/{product_id}", response_class=HTMLResponse)
async def edit_product_page(request: Request, product_id: int,
                            db: Session = Depends(get_db),
                            admin: str = Depends(get_current_admin)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id).first()
    return templates.TemplateResponse("edit.html",
                                      {"request": request, "product": product})


@app.post("/admin/edit/{product_id}")
async def edit_product_save(
        product_id: int,
        title: str = Form(...),
        price: int = Form(...),
        description: str = Form(...),
        image: UploadFile = File(None),
        new_gallery: Optional[List[UploadFile]] = File(None),
        specifications: str = Form(""),
        delete_gallery: List[str] = Form(default=[]),
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/admin", status_code=303)

    product.title = title
    product.price = price
    product.description = description
    product.specifications = specifications

    if image and image.filename:
        old_image_path = product.image_url.lstrip("/")
        if os.path.exists(old_image_path):
            os.remove(old_image_path)
        main_image_path = f"static/images/{image.filename}"
        with open(main_image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        product.image_url = f"/{main_image_path}"

    current_gallery = product.gallery_urls.split(
        ",") if product.gallery_urls else []
    current_gallery = [g for g in current_gallery if g]

    for del_img in delete_gallery:
        if del_img in current_gallery:
            current_gallery.remove(del_img)
            del_path = del_img.lstrip("/")
            if os.path.exists(del_path):
                os.remove(del_path)

    if new_gallery:
        for file in new_gallery:
            if file and file.filename:
                g_path = f"static/images/gal_{file.filename}"
                with open(g_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                current_gallery.append(f"/{g_path}")

    product.gallery_urls = ",".join(current_gallery)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


# --- ЗАКАЗ ТОВАРА (Асинхронный бот) ---
@app.post("/order")
async def process_order(
        product_id: int = Form(...),
        contact: str = Form(...),
        db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id).first()

    # Проверяем, что товар найден и токены загружены из .env
    if product and BOT_TOKEN and ADMIN_CHAT_ID:
        message_text = (
            f"🚀 <b>НОВЫЙ ЗАКАЗ С САЙТА!</b>\n\n"
            f"📦 <b>Товар:</b> {product.title}\n"
            f"💰 <b>Цена:</b> {product.price} ₽\n"
            f"👤 <b>Контакт клиента:</b> {contact}\n\n"
            f"Свяжитесь с ним для уточнения деталей доставки и оплаты."
        )

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": message_text,
            "parse_mode": "HTML"
        }

        # Используем httpx для отправки без зависания сервера
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json=payload)
            except Exception as e:
                print(f"Ошибка при отправке в Telegram: {e}")

    return RedirectResponse(url="/success", status_code=303)