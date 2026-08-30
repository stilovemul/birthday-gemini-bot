import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

from core.config import TELEGRAM_BOT_TOKEN, MSK_TZ
from core.scheduler import run_scheduler
from modules.birthdays.handlers import router as birthdays_router
from modules.birthdays.storage import get_sorted_birthdays, format_date_entry, format_age_word
from modules.notes.handlers import router as notes_router, load_notes
from modules.ai_assistant.handlers import router as ai_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SuperBotApp")

# Telegram Bot & Dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Register modular routers in logical order:
# Specific command routers first, AI catch-all router last!
dp.include_router(birthdays_router)
dp.include_router(notes_router)
dp.include_router(ai_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск супер-бота в облаке 24/7...")
    scheduler_task = asyncio.create_task(run_scheduler())
    polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    yield
    logger.info("Остановка приложения...")
    scheduler_task.cancel()
    polling_task.cancel()
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
@app.get("/healthz", response_class=HTMLResponse)
async def index():
    now_msk = datetime.now(MSK_TZ).strftime("%Y-%m-%d %H:%M:%S MSK")
    birthdays = get_sorted_birthdays()
    notes = load_notes()

    b_rows = ""
    for idx, item in enumerate(birthdays, 1):
        name = item["name"]
        d_str = format_date_entry(item)
        days = item["days_left"]
        age = format_age_word(item["turning_age"]) if item.get("turning_age") else "-"
        note = item.get("note", "")
        b_rows += f"<tr><td>{idx}</td><td><b>{name}</b></td><td>{d_str}</td><td>{age}</td><td>через {days} дн.</td><td>{note}</td></tr>"

    n_rows = ""
    for idx, n in enumerate(notes, 1):
        n_rows += f"<tr><td>{idx}</td><td>{n['text']}</td><td>{n['created_at']}</td><td><code>{n['id']}</code></td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>🤖 AiGemAntigravity Super-Bot Dashboard</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f1f5f9; padding: 30px; margin: 0; }}
            .container {{ max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.4); }}
            h1 {{ color: #38bdf8; margin-top: 0; }}
            .badge {{ display: inline-block; padding: 6px 14px; background: #10b981; color: white; border-radius: 20px; font-weight: bold; font-size: 14px; margin-bottom: 20px; }}
            .modules {{ display: flex; gap: 15px; margin-bottom: 25px; }}
            .card {{ flex: 1; background: #0f172a; padding: 15px; border-radius: 12px; border-left: 4px solid #38bdf8; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 30px; }}
            th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #334155; }}
            th {{ background: #0f172a; color: #94a3b8; font-size: 13px; text-transform: uppercase; }}
            h2 {{ color: #93c5fd; font-size: 18px; margin-top: 25px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AiGemAntigravity Super-Bot</h1>
            <div class="badge">🟢 СТАТУС: ОНЛАЙН В ОБЛАКЕ 24/7</div>
            <p>🕒 Время сервера: <b>{now_msk}</b> | Бот: <b>@MyAiGem_bot</b></p>
            
            <div class="modules">
                <div class="card">
                    <b>🤖 Gemini AI</b><br><span style="color:#94a3b8">Диалог, фото, память</span>
                </div>
                <div class="card">
                    <b>🎂 Дни рождения</b><br><span style="color:#94a3b8">{len(birthdays)} записей (09:00 MSK)</span>
                </div>
                <div class="card">
                    <b>📝 Заметки / Задачи</b><br><span style="color:#94a3b8">{len(notes)} сохраненных</span>
                </div>
            </div>

            <h2>🎂 Дни рождения ({len(birthdays)})</h2>
            <table>
                <thead>
                    <tr><th>#</th><th>Имя</th><th>Дата</th><th>Возраст</th><th>Осталось</th><th>Заметка</th></tr>
                </thead>
                <tbody>
                    {b_rows if b_rows else '<tr><td colspan="6">Список пуст</td></tr>'}
                </tbody>
            </table>

            <h2>📝 Быстрые заметки ({len(notes)})</h2>
            <table>
                <thead>
                    <tr><th>#</th><th>Текст</th><th>Создано</th><th>ID</th></tr>
                </thead>
                <tbody>
                    {n_rows if n_rows else '<tr><td colspan="4">Заметок пока нет</td></tr>'}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
