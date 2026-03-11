from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt, JWTError

import models
from database import get_db
from security import get_password_hash, verify_password, create_access_token, \
    SECRET_KEY, ALGORITHM

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПРОВЕРКИ АВТОРИЗАЦИИ ---
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        # Убираем префикс Bearer, если он есть
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(models.Customer).filter(
            models.Customer.email == email).first()
        return user
    except JWTError:
        return None


# --- СТРАНИЦА ВХОДА И РЕГИСТРАЦИИ ---
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/register")
async def register_user(
        email: str = Form(...),
        password: str = Form(...),
        name: str = Form(""),
        phone: str = Form(""),
        db: Session = Depends(get_db)
):
    # Проверяем, нет ли уже такого пользователя
    existing_user = db.query(models.Customer).filter(
        models.Customer.email == email).first()
    if existing_user:
        # Если есть, возвращаем на страницу входа (в идеале с сообщением об ошибке)
        return RedirectResponse(url="/login?error=email_exists",
                                status_code=303)

    new_user = models.Customer(
        email=email,
        password_hash=get_password_hash(password),
        name=name,
        phone=phone
    )
    db.add(new_user)
    db.commit()

    # Сразу авторизуем после регистрации
    access_token = create_access_token(data={"sub": new_user.email})
    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}",
                        httponly=True)
    return response


@router.post("/login")
async def login_user(
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(models.Customer).filter(
        models.Customer.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse(url="/login?error=wrong_credentials",
                                status_code=303)

    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}",
                        httponly=True)
    return response


@router.get("/logout")
async def logout_user():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


# --- ЛИЧНЫЙ КАБИНЕТ ---
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Получаем заказы пользователя, самые свежие сверху
    user_orders = db.query(models.Order).filter(
        models.Order.customer_id == user.id).order_by(
        models.Order.id.desc()).all()

    return templates.TemplateResponse("profile.html",
                                      {"request": request, "user": user,
                                       "orders": user_orders})