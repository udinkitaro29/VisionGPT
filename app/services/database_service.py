# app/services/database_service.py
import logging
import hashlib
from sqlalchemy.orm import Session
from app.database.models import Signal as SignalModel, User as UserModel, PaymentInvoice as PaymentInvoiceModel
from telegram import User as TelegramUser
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from app.core_logic.packages import PACKAGES, PACKAGE_ASSETS, SYMBOL_MAP
from app.utils.signal_classifier import classify_trading_style
from app.database.models import PaymentInvoice as PaymentInvoiceModel

logger = logging.getLogger(__name__)

# --- FUNGSI SINYAL (LOGIKA BARU) ---

def generate_signal_unique_id(signal_data: dict) -> str:
    """Membuat 'sidik jari' unik dari data inti sinyal."""
    id_string = (
        f"{signal_data.get('pair')}|{signal_data.get('timeframe')}|"
        f"{signal_data.get('pattern_name')}|{signal_data.get('entry_price')}|"
        f"{signal_data.get('take_profit')}|{signal_data.get('stop_loss')}"
    )
    return hashlib.md5(id_string.encode()).hexdigest()

def upsert_signal(db: Session, signal_data: dict) -> Tuple[SignalModel, bool]:
    """
    UPDATE sinyal jika sudah ada (berdasarkan unique_id), INSERT jika belum ada (Upsert).
    Mengembalikan tuple: (objek sinyal dari DB, boolean is_new).
    is_new akan True hanya jika sinyal baru pertama kali dibuat.
    """
        # --- PERUBAHAN UTAMA: NORMALISASI SIMBOL ---
    original_pair = signal_data.get('pair', '').upper()
    # Terjemahkan nama pair menggunakan SYMBOL_MAP, jika tidak ada, gunakan nama asli
    normalized_pair = SYMBOL_MAP.get(original_pair, original_pair)
    signal_data['pair'] = normalized_pair
    logger.info(f"Normalisasi simbol: '{original_pair}' -> '{normalized_pair}'")
    # --- AKHIR PERUBAHAN ---
    # Klasifikasikan gaya trading sebelum membuat unique_id atau menyimpan
    target_period = signal_data.get("target_period")
    trading_style = classify_trading_style(target_period)
    signal_data['trading_style'] = trading_style

    unique_id = generate_signal_unique_id(signal_data)
    
    existing_signal = db.query(SignalModel).filter(SignalModel.unique_id == unique_id).first()
    
    is_new = False
    if existing_signal:
        logger.debug(f"Sinyal lama ditemukan (ID: {existing_signal.id}). Mengupdate...")
        existing_signal.pattern_age = signal_data.get("pattern_age")
        existing_signal.last_seen_at = datetime.utcnow()
        # Update trading style jika berubah (jarang terjadi tapi untuk keamanan)
        if existing_signal.trading_style != trading_style:
            existing_signal.trading_style = trading_style
        db_signal = existing_signal
    else:
        logger.info(f"Sinyal baru terdeteksi (Unique ID: {unique_id}). Menyimpan ke DB...")
        is_new = True
        
        signal_data_to_save = signal_data.copy()
        signal_data_to_save['unique_id'] = unique_id
        
        allowed_keys = {c.name for c in SignalModel.__table__.columns}
        filtered_data = {k: v for k, v in signal_data_to_save.items() if k in allowed_keys}
        
        db_signal = SignalModel(**filtered_data)
        db.add(db_signal)
    
    db.commit()
    db.refresh(db_signal)
    return db_signal, is_new

def delete_inactive_signals(db: Session, active_unique_ids: List[str]):
    """Menghapus sinyal dari DB yang unique_id-nya tidak ada di daftar aktif."""
    if not active_unique_ids:
        logger.warning("Daftar sinyal aktif kosong, tidak ada yang dihapus untuk menghindari kesalahan.")
        return

    try:
        inactive_signals_query = db.query(SignalModel).filter(SignalModel.unique_id.notin_(active_unique_ids))
        num_deleted = inactive_signals_query.count()
        
        if num_deleted > 0:
            logger.info(f"Ditemukan {num_deleted} sinyal tidak aktif. Menghapus dari database...")
            inactive_signals_query.delete(synchronize_session=False)
            db.commit()
            logger.info(f"{num_deleted} sinyal tidak aktif berhasil dihapus.")
        else:
            logger.info("Database sudah sinkron. Tidak ada sinyal tidak aktif yang perlu dihapus.")
    except Exception as e:
        logger.error(f"Error saat menghapus sinyal tidak aktif: {e}", exc_info=True)
        db.rollback()

# --- FUNGSI USER & GET ---

def get_or_create_user(db: Session, telegram_user: TelegramUser) -> UserModel:
    db_user = db.query(UserModel).filter(UserModel.telegram_id == telegram_user.id).first()
    if db_user:
        if db_user.username != telegram_user.username or db_user.first_name != telegram_user.first_name:
            db_user.username, db_user.first_name = telegram_user.username, telegram_user.first_name
            db.commit()
        return db_user
    else:
        new_user = UserModel(telegram_id=telegram_user.id, username=telegram_user.username, first_name=telegram_user.first_name)
        db.add(new_user); db.commit(); db.refresh(new_user)
        return new_user

def update_user_subscription(db: Session, telegram_id: int, package_name: str, duration_days: int, package_type: str) -> Optional[UserModel]:
    db_user = get_user_by_telegram_id(db, telegram_id)
    if not db_user: return None
    end_date = datetime.now() + timedelta(days=duration_days)
    if package_type == 'addon':
        db_user.ea_subscription_status = "ACTIVE"
        db_user.ea_subscription_end_date = end_date
    else:
        db_user.main_subscription_status = "ACTIVE"
        db_user.main_package_name = package_name
        db_user.main_subscription_end_date = end_date
        if package_type == 'trial': db_user.is_trial_used = True
    db.commit(); db.refresh(db_user)
    return db_user

def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.telegram_id == telegram_id).first()

def get_user_allowed_assets(db: Session, telegram_id: int) -> List[str]:
    user = get_user_by_telegram_id(db, telegram_id)
    allowed_assets = []
    if user and user.main_subscription_status == "ACTIVE" and user.main_subscription_end_date > datetime.now():
        for key, details in PACKAGES.items():
            if details["name"] == user.main_package_name:
                allowed_assets.extend(details.get("assets", [])); break
    return [asset.upper() for asset in allowed_assets]

def toggle_user_notification_status(db: Session, telegram_id: int) -> Optional[UserModel]:
    user = get_user_by_telegram_id(db, telegram_id)
    if user: user.notifications_on = not user.notifications_on; db.commit(); db.refresh(user)
    return user

def get_subscribed_users_for_pair(db: Session, pair: str) -> List[UserModel]:
    if not pair: return []
    eligible_package_names = []
    for key, details in PACKAGES.items():
        if "assets" in details and pair.upper() in [a.upper() for a in details["assets"]]:
            eligible_package_names.append(details["name"])
    if not eligible_package_names: return []
    subscribed_users = db.query(UserModel).filter(
        UserModel.main_subscription_status == "ACTIVE",
        UserModel.main_subscription_end_date > datetime.now(),
        UserModel.notifications_on == True,
        UserModel.main_package_name.in_(eligible_package_names)
    ).all()
    logger.info(f"Ditemukan {len(subscribed_users)} pelanggan yang berhak untuk pair '{pair}'.")
    return subscribed_users

def get_signals_by_criteria(db: Session, telegram_id: int, pair: str, style: str) -> List[SignalModel]:
    allowed_assets = get_user_allowed_assets(db, telegram_id)
    if pair.upper() not in allowed_assets:
        logger.warning(f"User {telegram_id} mencoba akses pair {pair} yang tidak ada di paketnya.")
        return []
    signals = db.query(SignalModel).filter(
        SignalModel.pair == pair.upper(),
        SignalModel.trading_style == style
    ).order_by(SignalModel.id.desc()).limit(5).all()
    return signals

def toggle_auto_trade_status(db: Session, telegram_id: int) -> Optional[UserModel]:
    """Mengubah status auto_trade_enabled On/Off untuk user."""
    user = get_user_by_telegram_id(db, telegram_id)
    if user:
        # Hanya izinkan aktifasi auto-trade jika punya paket EA aktif
        has_ea_package = user.ea_subscription_status == "ACTIVE" and (user.ea_subscription_end_date is None or user.ea_subscription_end_date > datetime.now())
        if not has_ea_package and not user.auto_trade_enabled: # jika mau meng-ON-kan tapi tidak punya paket
            logger.warning(f"User {telegram_id} mencoba mengaktifkan auto-trade tanpa paket EA.")
            return None # Kembalikan None untuk menandakan aksi gagal

        user.auto_trade_enabled = not user.auto_trade_enabled
        db.commit()
        db.refresh(user)
        logger.info(f"User {telegram_id} mengubah status auto-trade menjadi: {user.auto_trade_enabled}")
        return user
    return None

def set_user_symbol_prefix(db: Session, telegram_id: int, prefix: str) -> Optional[UserModel]:
    """Menyimpan atau menghapus pengaturan prefiks simbol untuk user."""
    user = get_user_by_telegram_id(db, telegram_id)
    if user:
        # Jika user mengirim "kosong" atau "hapus", kita set ke None (tidak ada prefiks)
        user.symbol_prefix = None if prefix.lower() in ['kosong', 'hapus', 'none', ''] else prefix
        db.commit()
        db.refresh(user)
        logger.info(f"User {telegram_id} mengubah prefiks simbol menjadi: '{user.symbol_prefix}'")
        return user
    return None

def set_user_symbol_suffix(db: Session, telegram_id: int, suffix: str) -> Optional[UserModel]:
    """Menyimpan atau menghapus pengaturan sufiks simbol untuk user."""
    user = get_user_by_telegram_id(db, telegram_id)
    if user:
        # Jika user mengirim "kosong" atau "hapus", kita set ke None (tidak ada sufiks)
        user.symbol_suffix = None if suffix.lower() in ['kosong', 'hapus', 'none', ''] else suffix
        db.commit()
        db.refresh(user)
        logger.info(f"User {telegram_id} mengubah sufiks simbol menjadi: '{user.symbol_suffix}'")
        return user
    return None

# --- FUNGSI BARU UNTUK MANAJEMEN INVOICE ---

def create_payment_invoice(db: Session, user_id: int, ref_id: str, url: str, pkg_key: str) -> PaymentInvoiceModel:
    """Mencatat invoice pembayaran yang baru dibuat ke database dengan status PENDING."""
    logger.info(f"Mencatat invoice baru dengan reference_id: {ref_id} untuk user {user_id}")
    invoice = PaymentInvoiceModel(
        user_telegram_id=user_id,
        reference_id=ref_id,
        payment_url=url,
        package_key=pkg_key,
        status="PENDING"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

def update_invoice_status_on_success(db: Session, reference_id: str, trx_id: int) -> Optional[PaymentInvoiceModel]:
    """Mengubah status invoice menjadi PAID setelah pembayaran berhasil."""
    invoice = db.query(PaymentInvoiceModel).filter_by(reference_id=reference_id).first()
    if invoice and invoice.status == "PENDING":
        invoice.status = "PAID"
        invoice.paid_at = datetime.now()
        invoice.ipaymu_trx_id = trx_id
        db.commit()
        db.refresh(invoice)
        logger.info(f"Status invoice untuk reference_id {reference_id} diupdate menjadi PAID.")
        return invoice
    logger.warning(f"Invoice dengan reference_id {reference_id} tidak ditemukan atau statusnya bukan PENDING.")
    return None

def get_pending_invoices(db: Session) -> List[PaymentInvoiceModel]:
    """Mengambil semua invoice yang statusnya masih PENDING."""
    # Ambil invoice yang dibuat antara 24 jam yang lalu dan 1 jam yang lalu
    # untuk menghindari mengirim pengingat terlalu cepat atau untuk invoice yang sudah terlalu lama.
    one_hour_ago = datetime.now() - timedelta(hours=1)
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    
    pending_invoices = db.query(PaymentInvoiceModel).filter(
        PaymentInvoiceModel.status == "PENDING",
        PaymentInvoiceModel.created_at < one_hour_ago,
        PaymentInvoiceModel.created_at > twenty_four_hours_ago
    ).all()
    
    return pending_invoices