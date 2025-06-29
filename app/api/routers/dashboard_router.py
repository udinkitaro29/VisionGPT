# app/api/routers/dashboard_router.py
import logging
import secrets # <<< TAMBAHKAN IMPORT INI
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.database.models import Signal
from app.core_logic.config import AUTOCHARTIST_BASE_IFRAME_URL, DASHBOARD_USERNAME, DASHBOARD_PASSWORD
from dotenv import set_key, find_dotenv

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard UI"]
)

templates = Jinja2Templates(directory="templates")
security = HTTPBasic()

# Dependency untuk mendapatkan sesi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fungsi "penjaga" untuk otentikasi
def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Memvalidasi username dan password yang dimasukkan user."""
    # Pastikan kredensial dari config ada
    if not DASHBOARD_USERNAME or not DASHBOARD_PASSWORD:
        raise HTTPException(status_code=500, detail="Konfigurasi username/password dashboard belum diatur di server.")
        
    correct_username = secrets.compare_digest(credentials.username, DASHBOARD_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, DASHBOARD_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Terapkan "penjaga" ke semua endpoint di bawah ini dengan 'dependencies'
@router.get("/", response_class=HTMLResponse, dependencies=[Depends(authenticate_user)])
async def read_dashboard(request: Request, db: Session = Depends(get_db), message: str = ""):
    """Menampilkan halaman utama dashboard."""
    try:
        signals = db.query(Signal).order_by(Signal.id.desc()).all()
        current_url = AUTOCHARTIST_BASE_IFRAME_URL or "URL belum diatur di .env"
        return templates.TemplateResponse(
            "dashboard.html", 
            {"request": request, "signals": signals, "current_url": current_url, "message": message}
        )
    except Exception as e:
        logger.error(f"Gagal memuat dashboard: {e}", exc_info=True)
        return HTMLResponse(content=f"<h1>Error memuat dashboard: {e}</h1>", status_code=500)

@router.post("/update-url", dependencies=[Depends(authenticate_user)])
async def update_autochartist_url(new_url: str = Form(...)):
    """Menerima data dari form untuk memperbarui URL di file .env."""
    message = ""
    try:
        dotenv_path = find_dotenv()
        if not dotenv_path:
            with open(".env", "w") as f: pass # Buat file .env jika tidak ada
            dotenv_path = find_dotenv()
            
        set_key(dotenv_path, "AUTOCHARTIST_BASE_IFRAME_URL", new_url)
        message = "URL berhasil disimpan! Harap restart aplikasi agar scraper menggunakan URL baru."
        logger.info(message)
    except Exception as e:
        message = f"Gagal menyimpan URL: {e}"
        logger.error(message, exc_info=True)
    
    return RedirectResponse(url=f"/dashboard?message={message}", status_code=303)