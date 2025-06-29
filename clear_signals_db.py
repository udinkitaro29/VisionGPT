# clear_signals_db.py
from app.database.database import SessionLocal
from app.database.models import Signal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_signals_table():
    db = SessionLocal()
    try:
        logger.info("Mencoba menghapus semua data dari tabel 'signals'...")
        num_rows_deleted = db.query(Signal).delete()
        db.commit()
        logger.info(f"Berhasil! {num_rows_deleted} baris telah dihapus dari tabel 'signals'.")
    except Exception as e:
        logger.error(f"Terjadi error saat menghapus data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Script ini akan menghapus SEMUA data dari tabel 'signals'.")
    confirm = input("Apakah Anda yakin ingin melanjutkan? (y/n): ")
    if confirm.lower() == 'y':
        clear_signals_table()
    else:
        print("Aksi dibatalkan.")