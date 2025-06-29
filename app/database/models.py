# app/database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    
    # 'Sidik jari' unik untuk setiap sinyal, dibuat dari gabungan data inti.
    unique_id = Column(String, unique=True, index=True, nullable=False)

    pair = Column(String, index=True)
    timeframe = Column(String, nullable=True)
    # --- TAMBAHKAN KOLOM BARU ---
    trading_style = Column(String, index=True, nullable=True) # Scalper, Intraday, Swing
    # --- AKHIR TAMBAHAN ---
    pattern_name = Column(String, nullable=True)
    pattern_type = Column(String, nullable=True)
    pattern_age = Column(String, nullable=True) # Akan di-update terus
    
    entry_price = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    
    target_period = Column(String, nullable=True)
    expiry_datetime = Column(String, nullable=True)

    image_url = Column(String, nullable=True)
    short_description = Column(String, nullable=True)
    
    # Waktu pertama kali sinyal ini dibuat di DB
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Waktu terakhir kali scraper melihat sinyal ini masih aktif di web
    last_seen_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    
    is_trial_used = Column(Boolean, default=False)
    main_subscription_status = Column(String, default="NONE") # NONE, ACTIVE, EXPIRED
    main_package_name = Column(String, nullable=True)
    main_subscription_end_date = Column(DateTime, nullable=True)
    
    ea_subscription_status = Column(String, default="NONE")
    ea_subscription_end_date = Column(DateTime, nullable=True)
    
    notifications_on = Column(Boolean, default=True)
        # --- TAMBAHKAN KOLOM BARU ---
    auto_trade_enabled = Column(Boolean, default=False)
    # --- AKHIR TAMBAHAN ---
    # --- TAMBAHKAN DUA KOLOM BARU INI ---
    symbol_prefix = Column(String, nullable=True) # Untuk #, a., dll.
    symbol_suffix = Column(String, nullable=True) # Untuk .m, c, .pro, dll.
    # --- AKHIR TAMBAHAN ---

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PaymentInvoice(Base):
    __tablename__ = "payment_invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_telegram_id = Column(BigInteger, index=True, nullable=False)
    # ID unik yang kita kirim ke iPaymu
    reference_id = Column(String, unique=True, index=True, nullable=False)
    # ID unik dari iPaymu setelah transaksi berhasil
    ipaymu_trx_id = Column(BigInteger, nullable=True)

    payment_url = Column(String, nullable=False)
    package_key = Column(String, nullable=False)

    # Status: PENDING, PAID, EXPIRED
    status = Column(String, default="PENDING", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)