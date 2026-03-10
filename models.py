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
    price = Column(Integer)  # Это будет базовая цена
    description = Column(Text)
    category = Column(String, index=True)
    image_url = Column(String)
    gallery_urls = Column(Text, default="")
    specifications = Column(Text, default="")

    is_active = Column(Boolean, default=True)

    # ВНИМАНИЕ: Если у товара есть вариации, эти два поля станут "запасными" (для простых товаров без вариаций)
    in_stock = Column(Integer, default=0)
    is_made_to_order = Column(Boolean, default=True)

    # --- НОВОЕ: Связь с вариациями ---
    variants = relationship("ProductVariant", backref="product",
                            cascade="all, delete-orphan")


# --- НОВАЯ ТАБЛИЦА: Вариации товара (цвет, материал, размер) ---
class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))

    name = Column(String)  # Например: "Красный (ABS)", "Полупрозрачная смола"
    in_stock = Column(Integer, default=0)  # Индивидуальный остаток
    is_made_to_order = Column(Boolean, default=False)

    price_modifier = Column(Integer,
                            default=0)  # Добавка к базовой цене (например, +500 руб за сложный пластик)
    image_url = Column(String, default="")  # Специфичное фото для этой версии


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_contact = Column(String)
    customer_name = Column(String, default="")
    status = Column(String, default="Новый")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    total_price = Column(Integer, default=0)
    comment = Column(Text, default="")

    items = relationship("OrderItem", backref="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    # --- НОВОЕ: Привязка купленного айтема к конкретной вариации ---
    variant_id = Column(Integer, ForeignKey("product_variants.id"),
                        nullable=True)
    variant_name = Column(String,
                          default="")  # Сохраняем имя на случай, если вариацию потом удалят

    quantity = Column(Integer, default=1)
    price_at_order = Column(Integer)

    product = relationship("Product")
    # Добавляем связь с вариацией
    variant = relationship("ProductVariant")