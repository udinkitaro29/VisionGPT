# app/services/chatgpt_service.py
import logging
from openai import AsyncOpenAI
from app.core_logic.config import OPENAI_API_KEY
import json
from typing import Dict

logger = logging.getLogger(__name__)

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY tidak ditemukan. Fungsi analisis ChatGPT tidak akan bekerja.")
    client = None
else:
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("AsyncOpenAI client berhasil diinisialisasi.")
    except Exception as e:
        logger.error(f"Gagal menginisialisasi AsyncOpenAI client: {e}", exc_info=True)
        client = None

async def generate_enhanced_analysis(signal_data: Dict) -> Dict:
    """
    Menganalisis data sinyal lengkap menggunakan ChatGPT untuk:
    1. Menentukan Arah (BUY/SELL).
    2. Menghitung Risk:Reward.
    3. Membuat copywriting (penjelasan pola, ringkasan, prediksi).
    """
    if not client:
        logger.error("OpenAI client tidak diinisialisasi. Tidak dapat melakukan analisis.")
        return {"error": "OpenAI client not initialized"}

    # Siapkan data input untuk prompt dari dictionary sinyal yang di-scrape
    prompt_input_data = {
        "pair": signal_data.get("pair"),
        "timeframe": signal_data.get("timeframe"),
        "pattern_name": signal_data.get("pattern_name"),
        "pattern_type": signal_data.get("pattern_type"),
        "pattern_age": signal_data.get("pattern_age"),
        "entry_price": signal_data.get("entry_price"),
        "take_profit": signal_data.get("take_profit"),
        "stop_loss": signal_data.get("stop_loss"),
        "short_description": signal_data.get("short_description")
    }

    system_prompt = (
        "Anda adalah seorang analis trading Forex dan copywriter ahli berbahasa Indonesia. "
        "Tugas Anda adalah menerima data sinyal mentah dalam format JSON, menganalisisnya, "
        "dan mengembalikan hasil analisis lengkap dalam format JSON yang terstruktur. "
        "Lakukan semua kalkulasi dan penentuan yang diminta dengan akurat. "
        "Hanya kembalikan objek JSON, tanpa komentar atau teks tambahan."
    )
    
    user_prompt = f"""
    Analisis data sinyal berikut:
    {json.dumps(prompt_input_data, indent=2)}

    Berdasarkan data di atas, lakukan tugas-tugas berikut:
    1.  Tentukan 'direction' ('BUY' atau 'SELL'). Logikanya: jika take_profit > entry_price, maka 'BUY'. Jika take_profit < entry_price, maka 'SELL'.
    2.  Hitung 'rr_risk_points' sebagai nilai absolut dari |entry_price - stop_loss|.
    3.  Hitung 'rr_reward_points' sebagai nilai absolut dari |take_profit - entry_price|.
    4.  Hitung 'rr_ratio' sebagai (rr_reward_points / rr_risk_points), format menjadi 2 angka desimal. Jika risk adalah 0, kembalikan 0.
    5.  Buat 'pattern_explanation' dalam bahasa Indonesia untuk 'pattern_name' dan 'pattern_type' (misalnya, "Channel Down Emerging" menjadi "Kanal Turun Mulai Terbentuk").
    6.  Buat 'summary' (ringkasan) dalam 1 kalimat berdasarkan 'short_description'.
    7.  Buat 'prediction' (paragraf prediksi) yang memberikan analisis dan kesimpulan akhir yang menarik bagi trader.

    Kembalikan seluruh respons Anda dalam SATU OBJEK JSON TUNGGAL dengan kunci-kunci berikut:
    "direction", "rr_risk_points", "rr_reward_points", "rr_ratio", "pattern_explanation", "summary", "prediction".
    """

    logger.info(f"Mengirim permintaan analisis lengkap ke ChatGPT untuk pair {signal_data.get('pair')}")

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",  # Menggunakan model yang lebih canggih untuk hasil yang lebih baik
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        content = response.choices[0].message.content
        logger.debug(f"Respon mentah (content) dari ChatGPT: {content}")
        analysis_result = json.loads(content)
        logger.info(f"Analisis lengkap dari ChatGPT berhasil diterima dan di-parse.")
        return analysis_result
    except Exception as e:
        logger.error(f"Error saat berkomunikasi atau mem-parsing dari API OpenAI: {e}", exc_info=True)
        return {"error": f"OpenAI API error: {str(e)}"}