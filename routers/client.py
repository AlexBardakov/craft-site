from fastapi import APIRouter, Request, Depends, Form, status, JSONResponse
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from routers.customer import get_current_user
from delivery_service import calculate_delivery_cost

import models
from database import get_db

# Создаем роутер вместо app = FastAPI()
router = APIRouter()

# Шаблоны теперь подключаются здесь
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_home(request: Request, category: Optional[str] = None, db: Session = Depends(get_db)):
    # Теперь ВСЕГДА загружаем все активные товары, чтобы построить вкладки
    products = db.query(models.Product).filter(models.Product.is_active == True).all()
    categories = [c.name for c in db.query(models.Category).all()]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "products": products,
        "categories": categories,
        "active_category": category  # Передаем это для JS, чтобы открыть нужную вкладку
    })


@router.get("/info", response_class=HTMLResponse)
async def read_info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})


@router.get("/success", response_class=HTMLResponse)
async def read_success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@router.get("/contacts", response_class=HTMLResponse)
async def read_contacts(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})


@router.get("/terms", response_class=HTMLResponse)
async def read_terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def read_product(request: Request, product_id: int,
                       db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id,
                                              models.Product.is_active == True).first()
    if not product:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("product.html",
                                      {"request": request, "product": product})


@router.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request, db: Session = Depends(get_db)):
    # Пытаемся получить авторизованного пользователя
    user = get_current_user(request, db)
    # Передаем переменную user в шаблон
    return templates.TemplateResponse("cart.html", {"request": request, "user": user})


@router.post("/api/calculate-delivery")
async def api_calculate_delivery(
        city: str = Form(""),
        method: str = Form("Почта России")
):
    # Если город еще не ввели, возвращаем базовые цены
    if not city or len(city) < 2:
        default_cost = 350 if method == "Почта России" else 500
        return JSONResponse({"cost": default_cost})

    try:
        # Обращаемся к нашему сервису (и API СДЭК)
        cost = await calculate_delivery_cost(city, method)
        return JSONResponse({"cost": cost})
    except Exception as e:
        print(f"Ошибка API расчета: {e}")
        return JSONResponse(
            {"cost": 500})  # Отдаем базовый тариф при сбоях сети