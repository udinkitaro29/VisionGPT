# app/utils/text_utils.py
from typing import Optional, Dict

def escape_md(text: Optional[str]) -> str:
    """Meng-escape karakter khusus untuk Telegram MarkdownV2."""
    if text is None:
        return "N/A" # Kembalikan N/A jika nilai tidak ada, agar konsisten
    text = str(text)
    # Karakter titik ('.') sudah dihapus untuk angka desimal
    escape_chars = r'_*[]()~`>#+-=|{}!' 
    translator = str.maketrans({char: f"\\{char}" for char in escape_chars})
    return text.translate(translator)

def format_signal_message(signal_data: Dict) -> str:
    """
    Fungsi pusat untuk memformat dictionary sinyal menjadi pesan notifikasi standar.
    """
    # Tentukan Arah (BUY/SELL)
    entry = signal_data.get("entry_price")
    tp = signal_data.get("take_profit")
    direction = "N/A"
    if entry is not None and tp is not None:
        if tp > entry: direction = "BUY"
        elif tp < entry: direction = "SELL"

    # Siapkan semua komponen teks
    pair_name = "Gold Spot" if "XAU" in signal_data.get("pair", "") else signal_data.get("pair", "N/A")
    header_text = f"{pair_name} (TF: {signal_data.get('timeframe') or 'N/A'}) - {direction}"

    pattern_name = signal_data.get('pattern_name', 'N/A')
    pattern_type = signal_data.get('pattern_type', '')
    age = signal_data.get('pattern_age', 'N/A')
    pattern_info_text = f"Pola: {pattern_name}{f' ({pattern_type})' if pattern_type else ''} - Ditemukan pada: {age}"

    expiry_text = f"Expiry: {signal_data.get('expiry_datetime') or 'N/A'}"
    target_period_text = f"Target Period: {signal_data.get('target_period') or 'N/A'}"
    entry_text = signal_data.get("entry_price")
    tp_text = signal_data.get("take_profit")
    sl_text = signal_data.get("stop_loss")

    # Susun pesan notifikasi dengan format yang seragam
    message_parts = [
        f"🔔 *Sinyal Baru Ditemukan*",
        f"*{escape_md(header_text)}*",
        "\\-\\-\\-", # Separator aman
        escape_md(pattern_info_text),
        escape_md(expiry_text),
        escape_md(target_period_text),
        "", 
        f"💰 *Entry*: `{escape_md(entry_text)}`",
        f"🎯 *Take\\-Profit*: `{escape_md(tp_text)}`",
        f"❌ *Stop\\-Loss*: `{escape_md(sl_text)}`",
    ]

    message = "\n".join(message_parts)
    return message