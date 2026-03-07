from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Имя файла нашей базы данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./seaoddity.db"

# Создаем движок (engine).
# check_same_thread=False нужно специально для SQLite + FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создаем фабрику сессий (через них мы будем делать запросы)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс, от которого мы будем наследовать наши таблицы
Base = declarative_base()