from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, \
    DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(Integer)
    description = Column(Text)
    category = Column(String, index=True)
    image_url = Column(String)
    gallery_urls = Column(Text, default="")
    specifications = Column(Text, default="")

    # --- НОВЫЕ ПОЛЯ ДЛЯ МАСШТАБИРОВАНИЯ ---
    is_active = Column(Boolean, default=True)  # Показывать ли на сайте
    in_stock = Column(Integer, default=0)  # Количество готовых в наличии
    is_made_to_order = Column(Boolean,
                              default=True)  # Делается ли на заказ (требует времени)


# --- НОВЫЕ ТАБЛИЦЫ ДЛЯ БУДУЩЕЙ СИСТЕМЫ ЗАКАЗОВ ---

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_contact = Column(String)
    customer_name = Column(String, default="")
    status = Column(String, default="Новый")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    total_price = Column(Integer, default=0)
    comment = Column(Text, default="")

    # НОВОЕ: Связываем заказ с его содержимым (списком покупок)
    items = relationship("OrderItem", backref="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    price_at_order = Column(Integer)

    # НОВОЕ: Связываем строчку в чеке с конкретным товаром из базы
    product = relationship("Product")