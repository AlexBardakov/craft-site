from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Имя файла нашей базы данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./bureau.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- НОВОЕ: Перенесли функцию сюда из main.py ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()