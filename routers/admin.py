import os
import shutil
import secrets
import math
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import models
from database import get_db

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")
security = HTTPBasic()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

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


@router.get("/admin", response_class=HTMLResponse)
async def read_admin(
        request: Request,
        page: int = 1,  # <--- Принимаем номер страницы из URL
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    products = db.query(models.Product).all()
    categories = db.query(models.Category).all()

    # Настройки пагинации (показываем по 10 заказов на страницу)
    per_page = 10
    total_orders = db.query(models.Order).count()
    total_pages = math.ceil(total_orders / per_page) if total_orders > 0 else 1

    # Защита: если передали страницу меньше 1 или больше максимума
    if page < 1: page = 1
    if page > total_pages: page = total_pages

    # Загружаем только нужный кусок заказов
    orders = db.query(models.Order) \
        .order_by(models.Order.id.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "products": products,
        "categories": categories,
        "orders": orders,
        "current_page": page,
        "total_pages": total_pages
    })


@router.post("/admin/add")
async def add_product(
        title: str = Form(...),
        price: int = Form(...),
        description: str = Form(...),
        category: str = Form(...),
        image: UploadFile = File(...),
        gallery: Optional[List[UploadFile]] = File(None),
        specifications: str = Form(""),

        # НОВЫЕ ПОЛЯ:
        is_active: bool = Form(False),
        is_made_to_order: bool = Form(False),
        in_stock: int = Form(0),

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
        category=category,
        image_url=f"/{main_image_path}",
        gallery_urls=gallery_urls_str,
        specifications=specifications,

        # СОХРАНЯЕМ В БАЗУ:
        is_active=is_active,
        is_made_to_order=is_made_to_order,
        in_stock=in_stock
    )

    db.add(new_product)
    db.commit()
    return RedirectResponse(url="/admin?tab=products", status_code=303)

@router.post("/admin/delete/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@router.get("/admin/edit/{product_id}", response_class=HTMLResponse)
async def edit_product_page(request: Request, product_id: int, db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    categories = db.query(models.Category).all()
    return templates.TemplateResponse("edit.html", {"request": request, "product": product, "categories": categories})


@router.post("/admin/edit/{product_id}")
async def edit_product_save(
        product_id: int,
        title: str = Form(...),
        price: int = Form(...),
        description: str = Form(...),
        category: str = Form(...),
        image: UploadFile = File(None),
        new_gallery: Optional[List[UploadFile]] = File(None),
        specifications: str = Form(""),
        delete_gallery: List[str] = Form(default=[]),

        # НОВЫЕ ПОЛЯ:
        is_active: bool = Form(False),
        is_made_to_order: bool = Form(False),
        in_stock: int = Form(0),

        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/admin?tab=products", status_code=303)

    product.title = title
    product.price = price
    product.description = description
    product.category = category
    product.specifications = specifications

    # ОБНОВЛЯЕМ ДАННЫЕ В БАЗЕ:
    product.is_active = is_active
    product.is_made_to_order = is_made_to_order
    product.in_stock = in_stock

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
    return RedirectResponse(url="/admin?tab=products", status_code=303)

@router.post("/admin/category/add")
async def add_category(name: str = Form(...), db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    exists = db.query(models.Category).filter(models.Category.name == name).first()
    if not exists:
        new_cat = models.Category(name=name)
        db.add(new_cat)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/admin/category/delete/{cat_id}")
async def delete_category(cat_id: int, db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    cat = db.query(models.Category).filter(models.Category.id == cat_id).first()
    if cat:
        db.delete(cat)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/admin/order/{order_id}/status")
async def update_order_status(
        order_id: int,
        status: str = Form(...),
        page: int = Form(1), # Принимаем текущую страницу из скрытого поля
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    # Возвращаем пользователя на ту же страницу и на вкладку заказов
    return RedirectResponse(url=f"/admin?page={page}&tab=orders", status_code=303)

@router.post("/admin/product/{product_id}/quick_update")
async def quick_update_product(
        product_id: int,
        field: str = Form(...),
        value: str = Form(...),
        db: Session = Depends(get_db),
        admin: str = Depends(get_current_admin)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        # В зависимости от поля меняем нужный параметр
        if field == "is_active":
            product.is_active = (value.lower() == "true")
        elif field == "is_made_to_order":
            product.is_made_to_order = (value.lower() == "true")
        elif field == "in_stock":
            product.in_stock = int(value)
        db.commit()
        return JSONResponse(content={"status": "success"})
    return JSONResponse(content={"status": "error"}, status_code=404)