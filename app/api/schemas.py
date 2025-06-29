# app/api/schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class SignalBase(BaseModel):
    # Field yang sudah ada
    pair: str = Field(..., example="EURUSD")
    direction: str = Field(default="UNKNOWN", example="BUY")
    entry_price: Optional[float] = Field(None, example=1.0850)
    take_profit: Optional[float] = Field(None, example=1.0900)
    stop_loss: Optional[float] = Field(None, example=1.0820)
    source: str = Field("Manual Input", example="Autochartist")
    raw_description: str = Field(..., example="Aset: EURUSD (TF60)...")
    notes: Optional[str] = Field(None)
    image_url: Optional[HttpUrl] = Field(None)
    
    # --- FIELD BARU DARI SCRAPER (TAMBAHKAN INI) ---
    timeframe: Optional[str] = Field(None, example="60")
    pattern_name: Optional[str] = Field(None, example="Triangle")
    pattern_type: Optional[str] = Field(None, example="Emerging")
    pattern_age: Optional[str] = Field(None, example="2 hours ago")
    target_period: Optional[str] = Field(None, example="1 day")
    expiry_datetime: Optional[str] = Field(None, example="6/7 13:12")
    short_description: Optional[str] = Field(None, example="Triangle identified at...")
    # -------------------------------------------

class SignalCreate(SignalBase):
    """Model untuk membuat sinyal baru, baik dari API manual maupun dari scraper."""
    pass

class Signal(SignalBase):
    """Model untuk merepresentasikan sinyal setelah diproses."""
    # Untuk Pydantic v2
    model_config = {
        "from_attributes": True
    }
class TradeFeedback(BaseModel):
    telegram_id: int
    status: str # Akan berisi 'SUCCESS' atau 'FAILURE'
    ticket_id: Optional[int] = None
    symbol: str
    comment: Optional[str] = None
    order_type: str