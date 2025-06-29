# migrate_data.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Impor semua model dan konfigurasi Anda
from app.database.models import Base, User, Signal, PaymentInvoice
from app.core_logic.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataMigration")

# --- KONFIGURASI KONEKSI ---
# 1. Koneksi ke Database LAMA (SQLite)
SQLITE_DATABASE_URL = "sqlite:///signals.db" 
sqlite_engine = create_engine(SQLITE_DATABASE_URL)
SQLiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)

# 2. Koneksi ke Database BARU (PostgreSQL)
POSTGRES_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
postgres_engine = create_engine(POSTGRES_DATABASE_URL)
PostgresSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)

# Daftar semua model yang ingin kita migrasikan
MODELS_TO_MIGRATE = [User, Signal, PaymentInvoice]

def migrate_data():
    source_db = SQLiteSessionLocal()
    dest_db = PostgresSessionLocal()

    logger.info("Memulai proses migrasi data dari SQLite ke PostgreSQL...")

    try:
        for model in MODELS_TO_MIGRATE:
            table_name = model.__tablename__
            logger.info(f"--- Memigrasikan data untuk tabel: {table_name} ---")

            # Ambil semua data dari tabel sumber
            source_records = source_db.query(model).all()
            if not source_records:
                logger.info(f"Tidak ada data di tabel '{table_name}' untuk dimigrasikan. Dilewati.")
                continue

            logger.info(f"Ditemukan {len(source_records)} baris data. Memulai penyalinan...")
            
            count_success = 0
            count_skipped = 0

            for record in source_records:
                # Ubah record SQLAlchemy menjadi dictionary
                data = record.__dict__
                # Hapus state internal SQLAlchemy dan ID lama agar ID baru dibuat otomatis oleh PostgreSQL
                data.pop('_sa_instance_state', None)
                data.pop('id', None)

                # Buat objek baru dengan data dari sumber
                new_record = model(**data)
                
                # Tambahkan ke sesi tujuan
                dest_db.add(new_record)
                
                try:
                    # Coba commit satu per satu untuk menangani duplikasi jika ada
                    dest_db.commit()
                    count_success += 1
                except IntegrityError:
                    # Jika ada data duplikat (misal unique_id sudah ada), rollback dan lewati
                    logger.warning(f"Data duplikat ditemukan untuk tabel {table_name}, ID lama: {record.id}. Dilewati.")
                    dest_db.rollback()
                    count_skipped += 1
                except Exception as e:
                    logger.error(f"Error saat menyimpan record ke {table_name}: {e}")
                    dest_db.rollback()
                    count_skipped += 1

            logger.info(f"Selesai memigrasikan tabel '{table_name}'. Berhasil: {count_success}, Dilewati: {count_skipped}")

        logger.info("\nPROSES MIGRASI DATA SELESAI!")

    except Exception as e:
        logger.error(f"Terjadi error fatal saat migrasi: {e}", exc_info=True)
    finally:
        source_db.close()
        dest_db.close()
        logger.info("Koneksi ke kedua database telah ditutup.")


if __name__ == "__main__":
    print("Script ini akan menyalin data dari 'signals.db' (SQLite) ke database PostgreSQL Anda.")
    print("PASTIKAN Anda sudah menjalankan 'alembic upgrade head' di database PostgreSQL yang kosong.")
    print("PASTIKAN tidak ada data di tabel tujuan untuk menghindari duplikasi.")
    confirm = input("Apakah Anda yakin ingin memulai migrasi data sekarang? (y/n): ")
    
    if confirm.lower() == 'y':
        migrate_data()
    else:
        print("Migrasi dibatalkan.")