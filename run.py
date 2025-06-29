# run.py
import uvicorn
from app.api.main import app
from app.bot.core import telegram_app # <<< Impor objek telegram_app langsung

if __name__ == "__main__":
    # Di arsitektur kita, semua proses setup (termasuk pembuatan objek telegram_app)
    # sudah ditangani oleh 'lifespan' manager di dalam 'app/api/main.py'.
    # Namun, agar 'app.state' terisi dengan benar, kita perlu memastikan
    # objek bot yang sudah dibuat di 'lifespan' disimpan ke state.

    # Kode 'lifespan' di main.py sudah kita perbaiki untuk melakukan ini:
    # app.state.telegram_app = telegram_app
    
    # Oleh karena itu, file run.py ini bisa tetap sangat sederhana.
    # Error sebelumnya kemungkinan terjadi karena ada ketidaksesuaian
    # antara 'main.py' dan 'run.py'. Mari kita pastikan keduanya benar.
    
    # Pastikan 'main.py' Anda memiliki baris 'app.state.telegram_app = telegram_app'
    # di dalam fungsi 'lifespan' setelah 'setup_bot_application()'.
    
    # Jalankan server FastAPI. Ia akan otomatis menjalankan 'lifespan'.
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=8000, reload=True)