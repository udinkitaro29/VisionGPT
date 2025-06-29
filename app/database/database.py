# app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core_logic.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# --- KEMBALIKAN KE FORMAT STANDAR (akan otomatis menggunakan psycopg2) ---
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)