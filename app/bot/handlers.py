# app/bot/handlers.py
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from app.database.database import SessionLocal
from app.services import database_service, ipaymu_service, trading_service
from app.core_logic.packages import PACKAGES 
from app.utils.text_utils import escape_md, format_signal_message
from app.core_logic.config import PUBLIC_SERVER_URL

logger = logging.getLogger(__name__)

# --- Fungsi untuk Membangun Menu Keyboard ---

def build_subscriber_menu(user: database_service.UserModel) -> InlineKeyboardMarkup:
    """Membangun menu untuk pengguna yang berlangganan."""
    notif_status_text = "🔔 Notifikasi: ON" if user.notifications_on else "🔕 Notifikasi: OFF"
    auto_trade_status_text = "🤖 Trading Otomatis: ON" if user.auto_trade_enabled else "🤖 Trading Otomatis: OFF"
    has_ea_package = user.ea_subscription_status == "ACTIVE" and (user.ea_subscription_end_date is None or user.ea_subscription_end_date > datetime.now())
    
    keyboard = [
        [InlineKeyboardButton("📈 Riwayat Sinyal", callback_data='on_demand_start')],
        [InlineKeyboardButton("🛒 Beli/Upgrade Paket", callback_data='show_packages')],
        [InlineKeyboardButton(notif_status_text, callback_data='toggle_notifications')],
    ]
    
    if has_ea_package:
        # Hanya tampilkan tombol trading jika punya paket EA
        keyboard.append([InlineKeyboardButton(auto_trade_status_text, callback_data='auto_trade_menu')])
        
    keyboard.append([InlineKeyboardButton("⭐️ Status Langganan", callback_data='subscription_status')])
    keyboard.append([InlineKeyboardButton("⚙️ Pengaturan Akun", callback_data='account_settings')])
    keyboard.append([InlineKeyboardButton("☎️ Customer Support", url="https://t.me/alwaysrighttt")])
    
    return InlineKeyboardMarkup(keyboard)

def build_nonsubscriber_menu() -> InlineKeyboardMarkup:
    """Membangun menu untuk pengguna yang tidak berlangganan."""
    keyboard = [
        [InlineKeyboardButton("🛒 Beli Langganan", callback_data='show_packages')],
        [InlineKeyboardButton("ℹ️ Tentang Bot", callback_data='about_bot')],
        [InlineKeyboardButton("☎️ Customer Support", url="https://t.me/alwaysrighttt")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = update.effective_user; db = SessionLocal()
    try:
        database_service.get_or_create_user(db, telegram_user=user_data)
        await update.message.reply_html(rf"Halo {user_data.mention_html()}! Selamat datang di Bot Sinyal Trading.")
        await menu_command(update, context)
    finally: db.close()

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id; db = SessionLocal()
    try:
        user = database_service.get_user_by_telegram_id(db, user_id)
        is_subscribed = user and user.main_subscription_status == "ACTIVE" and (user.main_subscription_end_date is None or user.main_subscription_end_date > datetime.now())
        if is_subscribed:
            reply_markup, message_text = build_subscriber_menu(user), "Menu Pelanggan:"
        else:
            reply_markup, message_text = build_nonsubscriber_menu(), "Untuk mengakses fitur, silakan berlangganan:"
        if update.callback_query and update.callback_query.message:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
    except BadRequest as e:
        if 'Message is not modified' not in str(e): logger.warning(f"Gagal mengedit menu: {e}")
    finally: db.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk perintah /help. Menampilkan detail konfigurasi untuk klien."""
    user = update.effective_user
    logger.info(f"User {user.id} meminta bantuan dengan /help.")

    if not PUBLIC_SERVER_URL:
        await update.message.reply_text("Konfigurasi server belum lengkap. Harap hubungi admin.")
        return

    websocket_url = f"wss://{PUBLIC_SERVER_URL}/ws/"
    telegram_id = user.id
    
    # Rakit pesan sebagai teks biasa
    opening_text = "Berikut adalah detail konfigurasi untuk Klien Eksekutor Anda.\n\nSalin-tempel konten di bawah ini ke dalam file `config.ini` Anda:"
    
    config_content = (
        f"[SERVER]\n"
        f"WEBSOCKET_URL = {websocket_url}\n\n"
        f"[USER]\n"
        f"TELEGRAM_ID = {telegram_id}\n\n"
        f"[TRADING]\n"
        f"LOT_SIZE = 0.01\n"
        f"SLIPPAGE = 10\n\n"
        f"Masih Bingung Pelajari Selengkapnya\n"
        f"PANDUAN PENGGUNAAN\n"
        f"Video Panduan Penggunaan\n\n"

        f"Versi Reguler Tanpa Pro EA ( Tanpa Trading Otomatis)\n"
        f"https://youtu.be/P7pfYjW2SgE?si=59rnvGLwmtHMsSJx\n\n"

        f"Versi Pro EA (trading Otomatis dari Telegram\n"
        f"https://www.youtube.com/watch?v=YSdt7E31gmw\n\n"

        f"File Client\n"
        f"https://drive.google.com/drive/folders/1qPLUyf1R_W_zhHkl-kVwHy045oiXkhcH?usp=sharing\n"
    )
    
    # Gabungkan dengan ``` untuk visual, tapi kirim sebagai plain text
    final_message = f"{opening_text}\n\n```\n{config_content}```"

    # --- PERBAIKAN: Hapus parse_mode="MarkdownV2" ---
    await update.message.reply_text(final_message)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menampilkan menu pengaturan akun."""
    keyboard = [
        [InlineKeyboardButton("✍️ Atur Prefiks Simbol", callback_data='set_symbol_prefix')],
        [InlineKeyboardButton("✍️ Atur Sufiks Simbol", callback_data='set_symbol_suffix')],
        [InlineKeyboardButton("« Kembali ke Menu Utama", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = "Menu Pengaturan Akun:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    next_step = context.user_data.get('next_step')
    if not next_step:
        await update.message.reply_text("Gunakan perintah /menu untuk berinteraksi.")
        return
    db = SessionLocal()
    try:
        if next_step == 'set_prefix':
            database_service.set_user_symbol_prefix(db, user_id, text)
            await update.message.reply_text(f"✅ Pengaturan *Prefiks* disimpan: `{escape_md(text)}`", parse_mode="MarkdownV2")
        elif next_step == 'set_suffix':
            database_service.set_user_symbol_suffix(db, user_id, text)
            await update.message.reply_text(f"✅ Pengaturan *Sufiks* disimpan: `{escape_md(text)}`", parse_mode="MarkdownV2")
    finally: db.close()
    
    del context.user_data['next_step']
    await menu_command(update, context)


# --- BUTTON HANDLER (CALLBACK QUERY) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id; callback_data = query.data
    logger.info(f"User {user_id} menekan tombol dengan callback_data: '{callback_data}'")
    
    db = SessionLocal()
    try:
        async def proceed_to_create_invoice(package_key: str):
            pkg_details = PACKAGES.get(package_key)
            await query.edit_message_text(text=f"Anda memilih: {pkg_details['name']}.\nMembuat link pembayaran...")
            invoice_url = ipaymu_service.create_payment_link(telegram_id=user_id, package_key=package_key)
            if invoice_url: await query.message.reply_text(f"Silakan selesaikan pembayaran untuk paket '{pkg_details['name']}'", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("☑️ Bayar Sekarang", url=invoice_url)]]))
            else: await query.edit_message_text(text="Gagal membuat link pembayaran.")

        if callback_data == 'main_menu': await menu_command(update, context)
        elif callback_data == 'account_settings': await settings_command(update, context)

        elif callback_data == 'show_packages':
            keyboard = [[InlineKeyboardButton(f"{details['name']} - Rp {details['price']:,}".replace(',', '.'), callback_data=f'subscribe_{key}')] for key, details in PACKAGES.items()]
            keyboard.append([InlineKeyboardButton("« Kembali", callback_data='main_menu')])
            await query.edit_message_text(text="Pilih paket langganan:", reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif callback_data.startswith('subscribe_'):
            package_key = callback_data.replace('subscribe_', '')
            selected_package = PACKAGES.get(package_key)
            db_user = database_service.get_user_by_telegram_id(db, user_id)
            if not selected_package: return await query.edit_message_text(text="Paket tidak valid.")
            pkg_type = selected_package['type']
            if pkg_type == 'trial' and db_user.is_trial_used:
                await query.edit_message_text("Maaf, Anda sudah pernah menggunakan masa trial.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali", callback_data='show_packages')]]))
            elif pkg_type == 'addon' and not (db_user.main_subscription_status == "ACTIVE" and db_user.main_subscription_end_date > datetime.now()):
                await query.edit_message_text("Anda harus memiliki paket utama yang aktif untuk membeli Add-on ini.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali", callback_data='show_packages')]]))
            elif pkg_type == 'main' and db_user.main_subscription_status == "ACTIVE" and db_user.main_subscription_end_date > datetime.now() and db_user.main_package_name != selected_package['name']:
                warning_text = (f"PERINGATAN:\nAnda sudah memiliki paket *{escape_md(db_user.main_package_name)}*\\.\n\nMelanjutkan akan **MENGGANTIKAN** paket Anda saat ini dengan *{escape_md(selected_package['name'])}* dan masa aktif akan dihitung ulang\\. Langganan lama akan hangus\\.\n\nApakah Anda yakin?")
                keyboard = [[InlineKeyboardButton(f"Ya, Ganti ke {selected_package['name']}", callback_data=f"confirm_replace_{package_key}")], [InlineKeyboardButton("Tidak, Kembali", callback_data='show_packages')]]
                await query.edit_message_text(warning_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="MarkdownV2")
            else: await proceed_to_create_invoice(package_key)
        
        elif callback_data.startswith('confirm_replace_'):
            package_key = callback_data.replace('confirm_replace_', '')
            await proceed_to_create_invoice(package_key)

        elif callback_data == 'subscription_status':
            db_user = database_service.get_user_by_telegram_id(db, user_id)
            status_text = (f"*Status Langganan Anda:*\n\n*Paket Utama*: {escape_md(db_user.main_package_name or 'Tidak Ada')}\n*Status*: {escape_md(db_user.main_subscription_status)}\n*Berakhir pada*: {escape_md(db_user.main_subscription_end_date.strftime('%d %B %Y') if db_user.main_subscription_end_date else 'N/A')}\n\n*Paket Add\\-on EA*: {escape_md(db_user.ea_subscription_status)}\n*Berakhir pada*: {escape_md(db_user.ea_subscription_end_date.strftime('%d %B %Y') if db_user.ea_subscription_end_date else 'N/A')}")
            await query.edit_message_text(text=status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali", callback_data='main_menu')]]), parse_mode="MarkdownV2")
        
        elif callback_data == 'toggle_notifications':
            database_service.toggle_user_notification_status(db, user_id)
            await menu_command(update, context)

        elif callback_data == 'on_demand_start':
            user_allowed_assets = database_service.get_user_allowed_assets(db, user_id)
            if not user_allowed_assets: await query.edit_message_text("Paket langganan Anda tidak mencakup aset apapun.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Kembali", callback_data='main_menu')]]))
            else:
                keyboard = [[InlineKeyboardButton(asset, callback_data=f'select_pair_{asset}')] for asset in sorted(list(set(user_allowed_assets)))]
                keyboard.append([InlineKeyboardButton("« Kembali", callback_data='main_menu')])
                await query.edit_message_text("Silakan pilih Pair:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif callback_data.startswith('select_pair_'):
            pair = callback_data.replace('select_pair_', '', 1)
            keyboard = [[InlineKeyboardButton("Scalper", callback_data=f'show_style_{pair}_Scalper')], [InlineKeyboardButton("Intraday", callback_data=f'show_style_{pair}_Intraday')], [InlineKeyboardButton("Swing", callback_data=f'show_style_{pair}_Swing')], [InlineKeyboardButton("« Kembali Pilih Pair", callback_data='on_demand_start')]]
            await query.edit_message_text(f"Pilih Gaya Trading untuk *{escape_md(pair)}*:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="MarkdownV2")

        elif callback_data.startswith('show_style_'):
            parts = callback_data.replace('show_style_', '').split('_', 1); pair, style = parts[0], parts[1]
            signals = database_service.get_signals_by_criteria(db, user_id, pair, style)
            keyboard = [[InlineKeyboardButton("« Kembali Pilih Gaya", callback_data=f'select_pair_{pair}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if not signals:
                await query.edit_message_text(f"Tidak ditemukan riwayat sinyal untuk *{escape_md(pair)}* dengan gaya *{escape_md(style)}*\\.", reply_markup=reply_markup, parse_mode="MarkdownV2")
            else:
                await query.delete_message()
                await context.bot.send_message(chat_id=user_id, text=f"Riwayat 5 Sinyal Terakhir untuk *{escape_md(pair)}* Gaya *{escape_md(style)}*:", parse_mode="MarkdownV2")
                db_user = database_service.get_user_by_telegram_id(db, user_id)
                has_ea_package = db_user.ea_subscription_status == "ACTIVE" and (db_user.ea_subscription_end_date and db_user.ea_subscription_end_date > datetime.now())
                for s in signals:
                    signal_message = format_signal_message(s.__dict__).replace("🔔 *Sinyal Baru Ditemukan*", "📈 *Riwayat Sinyal*")
                    reply_markup_signal = InlineKeyboardMarkup([[InlineKeyboardButton("👆 Trading Manual", callback_data=f"manual_trade_start_{s.id}")]]) if has_ea_package else None
                    await context.bot.send_message(chat_id=user_id, text=signal_message, parse_mode="MarkdownV2", reply_markup=reply_markup_signal)
                    await asyncio.sleep(0.3)
                await context.bot.send_message(chat_id=user_id, text="Pilih Aksi Berikutnya:", reply_markup=reply_markup)
        
        elif callback_data == 'auto_trade_menu':
            updated_user = database_service.toggle_auto_trade_status(db, user_id)
            if updated_user:
                status_text = "AKTIF" if updated_user.auto_trade_enabled else "NONAKTIF"
                await context.bot.send_message(chat_id=user_id, text=f"🤖 Status Trading Otomatis Anda sekarang: *{escape_md(status_text)}*", parse_mode="MarkdownV2")
            else:
                await context.bot.send_message(chat_id=user_id, text="Gagal mengubah status. Anda mungkin memerlukan paket Add-on PRO EA.")
            await menu_command(update, context)

        elif callback_data.startswith('manual_trade_start_'):
            try:
                signal_id = int(callback_data.replace('manual_trade_start_', ''))
                keyboard = [[InlineKeyboardButton("📈 Eksekusi Market", callback_data=f'execute_{signal_id}_market')], [InlineKeyboardButton("⏳ Order Limit/Stop", callback_data=f'execute_{signal_id}_pending')], [InlineKeyboardButton("« Batal", callback_data='cancel_trade')]]
                await query.edit_message_text(f"Pilih tipe eksekusi untuk sinyal ID {signal_id}:", reply_markup=InlineKeyboardMarkup(keyboard))
            except (ValueError, IndexError): await query.edit_message_text("Sinyal tidak valid.")
            
        elif callback_data.startswith('execute_'):
            try:
                parts = callback_data.replace('execute_', '').split('_', 1); signal_id, order_type = int(parts[0]), parts[1]
            except (ValueError, IndexError): await query.edit_message_text("Perintah eksekusi tidak valid."); return
            signal = db.query(database_service.SignalModel).filter(database_service.SignalModel.id == signal_id).first()
            if not signal: await query.edit_message_text("Sinyal tidak lagi valid."); return
            signal_dict = {c.name: getattr(signal, c.name) for c in signal.__table__.columns}
            if signal.entry_price is not None and signal.take_profit is not None:
                signal_dict["direction"] = "BUY" if signal.take_profit > signal.entry_price else "SELL"
            message_text = f"Mengirim perintah eksekusi *{escape_md(order_type.upper())}* untuk *{escape_md(signal.pair)}*\\.\\.\\."
            await query.edit_message_text(text=message_text, parse_mode="MarkdownV2")
            await trading_service.send_trade_command_to_client(user_id, signal_dict, order_type)
            await query.message.reply_text(f"✅ Perintah '{order_type.upper()}' untuk {signal.pair} telah dikirim ke Klien Eksekutor Anda.")

        elif callback_data == 'cancel_trade' or callback_data == 'about_bot':
            message = "Aksi dibatalkan." if callback_data == 'cancel_trade' else "Bot ini menyediakan sinyal trading dari ."
            await query.edit_message_text(message)
            await asyncio.sleep(1)
            await menu_command(update, context)
        
        elif callback_data == 'set_symbol_prefix':
            context.user_data['next_step'] = 'set_prefix'
            await query.edit_message_text("Silakan kirimkan **PREFIKS** simbol Anda (contoh: `#` atau `a.`).\nKirim `kosong` jika tidak ada.")
        
        elif callback_data == 'set_symbol_suffix':
            context.user_data['next_step'] = 'set_suffix'
            await query.edit_message_text("Silakan kirimkan **SUFIKS** simbol Anda (contoh: `.m` atau `c`).\nKirim `kosong` jika tidak ada.")
            
        else:
            await context.bot.send_message(chat_id=user_id, text=f"Fitur untuk '{callback_data}' akan segera hadir!")
    except Exception as e:
        logger.error(f"Terjadi error di dalam button_handler untuk callback '{callback_data}': {e}", exc_info=True)
    finally:
        db.close()