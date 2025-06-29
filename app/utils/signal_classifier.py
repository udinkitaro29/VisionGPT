# app/utils/signal_classifier.py
import re
import logging

logger = logging.getLogger(__name__)

def classify_trading_style(target_period: str) -> str:
    """
    Mengklasifikasikan gaya trading berdasarkan string target_period.
    Contoh input: "1 day", "16 hours", "9 days"
    """
    if not target_period or not isinstance(target_period, str):
        return "Unknown"

    period_lower = target_period.lower()

    try:
        # Cari angka dan satuan waktu
        match = re.search(r'(\d+)\s*(hour|day|week|month)', period_lower)
        if not match:
            return "Unknown"

        value = int(match.group(1))
        unit = match.group(2)

        # Konversi semua ke jam untuk perbandingan yang mudah
        hours = 0
        if "hour" in unit:
            hours = value
        elif "day" in unit:
            hours = value * 24

        # Terapkan aturan klasifikasi Anda
        if 1 <= hours <= 3:
            return "Scalper"
        elif 4 <= hours <= 24: # 4 jam hingga 1 hari
            return "Intraday"
        elif hours > 24: # Lebih dari 1 hari (misalnya 2 days)
            return "Swing"
        else:
            return "Unknown"

    except Exception as e:
        logger.error(f"Error saat mengklasifikasikan target_period '{target_period}': {e}")
        return "Unknown"