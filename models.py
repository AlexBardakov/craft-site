from sqlalchemy import Column, Integer, String, Text
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(Integer)
    description = Column(Text)
    image_url = Column(String)
    gallery_urls = Column(Text, default="")
    specifications = Column(Text, default="")