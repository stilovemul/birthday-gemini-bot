import asyncio
import logging
import os
import aiohttp
from contextlib import asynccontextmanager
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

from core.config import TELEGRAM_BOT_TOKEN, MSK_TZ
from core.scheduler import run_scheduler
from modules.smart_home.handlers import router as smart_home_router
from modules.morning_digest.handlers import router as digest_router
from modules.birthdays.handlers import router as birthdays_router
from modules.birthdays.storage import get_sorted_birthdays, format_date_entry, format_age_word
from modules.notes.handlers import router as notes_router, load_notes
from modules.smart_reminders.handlers import router as reminders_router
from modules.smart_reminders.storage import get_active_reminders
from modules.image_gen.handlers import router as image_gen_router
from modules.food_tracker.handlers import router as food_router
from modules.drive2_tracker.handlers import router as drive2_router
from modules.vk_tracker.handlers import router as vk_router
from modules.max_tracker.handlers import router as max_router
from modules.secret_vault.handlers import router as vault_router
from modules.weather_synoptic.handlers import router as weather_router
from modules.sleep_calculator.handlers import router as sleep_router
from modules.loan_calculator.handlers import router as loan_router
from modules.webapp.router import router as webapp_router
from modules.webapp.handlers import router as webapp_bot_router
from modules.voice_assistant.handlers import router as voice_router
from modules.subscription_tracker.handlers import router as subs_router
from modules.custom_rules.handlers import router as rules_router
from modules.ai_assistant.handlers import router as ai_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SuperBotApp")

from aiogram.fsm.storage.memory import MemoryStorage

# Telegram Bot & Dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Register modular routers in logical order:
dp.include_router(digest_router)
dp.include_router(smart_home_router)
dp.include_router(voice_router)
dp.include_router(drive2_router)
dp.include_router(vk_router)
dp.include_router(max_router)
dp.include_router(loan_router)
dp.include_router(sleep_router)
dp.include_router(vault_router)
dp.include_router(weather_router)
dp.include_router(food_router)
dp.include_router(image_gen_router)
dp.include_router(reminders_router)
dp.include_router(birthdays_router)
dp.include_router(notes_router)
dp.include_router(subs_router)
dp.include_router(rules_router)
dp.include_router(webapp_bot_router)
dp.include_router(ai_router)  # Catch-all AI router last


async def keep_alive_task():
    """Pings the public web service URL every 5 minutes to prevent Render free-tier sleep."""
    app_url = "https://birthday-gemini-bot.onrender.com/healthz"
    logger.info(f"Запущена служба поддержания активности (Keep-Alive Self-Ping): {app_url}")
    await asyncio.sleep(60)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(app_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    logger.info(f"Keep-Alive ping status: {resp.status}")
        except Exception as e:
            logger.warning(f"Keep-Alive ping warning: {e}")
        await asyncio.sleep(300)


async def run_resilient_polling():
    """Runs Telegram polling with auto-reconnect on network interruptions."""
    while True:
        try:
            logger.info("Запуск Telegram Polling...")
            await bot.delete_webhook(drop_pending_updates=False)
            await dp.start_polling(bot, handle_signals=False)
        except Exception as e:
            logger.error(f"Polling interrupted: {e}. Перезапуск через 3 сек...")
            await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск супер-бота в облаке 24/7 (AI + Smart Home + Digest + Drive2 + VK + MAX + Кредиты + Сон + Сейф + Погода + КБЖУ)...")
    
    # Register official Telegram menu commands
    try:
        commands = [
            types.BotCommand(command="start", description="🏠 Главное меню"),
            types.BotCommand(command="app", description="📱 Открыть Mini App дашборд"),
            types.BotCommand(command="digest", description="🌅 Утренний персональный дайджест"),
            types.BotCommand(command="home", description="🏠 Управление Умным домом"),
            types.BotCommand(command="drive2", description="🚗 Мониторинг Drive2.ru"),
            types.BotCommand(command="vk", description="🔵 Мониторинг ВКонтакте"),
            types.BotCommand(command="max", description="💬 Мониторинг MAX (web.max.ru)"),
            types.BotCommand(command="credit", description="🔢 Кредиты, ипотека и досрочка"),
            types.BotCommand(command="sleep", description="😴 Калькулятор фаз сна"),
            types.BotCommand(command="weather", description="🌤 Погода и прогноз"),
            types.BotCommand(command="set_city", description="🏙 Установить мой город/район"),
            types.BotCommand(command="vault", description="🔐 Секретный сейф заметок"),
            types.BotCommand(command="food", description="🥗 Дневной рацион и калории"),
            types.BotCommand(command="image", description="🎨 Сгенерировать фото"),
            types.BotCommand(command="remind", description="⏰ Умное напоминание"),
            types.BotCommand(command="reminders", description="📋 Мои напоминания"),
            types.BotCommand(command="when", description="🎂 Узнать дату дня рождения"),
            types.BotCommand(command="clear", description="🧹 Очистить диалог с ИИ"),
            types.BotCommand(command="add", description="🎂 Добавить день рождения"),
            types.BotCommand(command="list", description="🎂 Список дней рождения"),
            types.BotCommand(command="note", description="📝 Быстрая заметка"),
            types.BotCommand(command="notes", description="📝 Список всех заметок"),
            types.BotCommand(command="help", description="❓ Справка по командам")
        ]
        await bot.set_my_commands(commands)
        logger.info("Команды Telegram успешно зарегистрированы в меню!")

        # Setup Telegram Menu Button (WebApp)
        await bot.set_chat_menu_button(
            menu_button=types.MenuButtonWebApp(
                type="web_app",
                text="📱 Дашборд",
                web_app=types.WebAppInfo(url="https://birthday-gemini-bot.onrender.com/app")
            )
        )
        logger.info("Кнопка MenuButtonWebApp успешно установлена!")
    except Exception as e:
        logger.error(f"Не удалось установить команды/MenuButton бота: {e}")

    scheduler_task = asyncio.create_task(run_scheduler(bot))
    polling_task = asyncio.create_task(run_resilient_polling())
    keepalive_task = asyncio.create_task(keep_alive_task())
    
    yield
    
    logger.info("Остановка приложения...")
    scheduler_task.cancel()
    polling_task.cancel()
    keepalive_task.cancel()
    await bot.session.close()


app = FastAPI(lifespan=lifespan)
app.include_router(webapp_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "AiGemAntigravity", "time": datetime.now(MSK_TZ).isoformat()}


@app.get("/", response_class=HTMLResponse)
async def index():
    now_msk = datetime.now(MSK_TZ).strftime("%Y-%m-%d %H:%M:%S MSK")
    birthdays = get_sorted_birthdays()
    notes = load_notes()
    reminders = get_active_reminders()

    b_rows = ""
    for idx, item in enumerate(birthdays, 1):
        name = item["name"]
        d_str = format_date_entry(item)
        days = item["days_left"]
        age = format_age_word(item["turning_age"]) if item.get("turning_age") else "-"
        note = item.get("note", "")
        b_rows += f"<tr><td>{idx}</td><td><b>{name}</b></td><td>{d_str}</td><td>{age}</td><td>через {days} дн.</td><td>{note}</td></tr>"

    r_rows = ""
    for idx, r in enumerate(reminders, 1):
        r_rows += f"<tr><td>{idx}</td><td><b>{r['text']}</b></td><td>{r['target_display']}</td><td><code>{r['id']}</code></td></tr>"

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
            .modules {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 25px; }}
            .card {{ background: #0f172a; padding: 14px; border-radius: 12px; border-left: 4px solid #38bdf8; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px; }}
            th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #334155; }}
            th {{ background: #0f172a; color: #94a3b8; font-size: 13px; text-transform: uppercase; }}
            h2 {{ color: #93c5fd; font-size: 18px; margin-top: 25px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AiGemAntigravity Super-Bot</h1>
            <div class="badge">🟢 СТАТУС: ОНЛАЙН В ОБЛАКЕ 24/7</div>
            <a href="/app" style="display:inline-block; margin-bottom: 20px; margin-left: 10px; padding: 6px 14px; background: #06b6d4; color: #0b0f19; border-radius: 20px; font-weight: bold; font-size: 14px; text-decoration: none; box-shadow: 0 0 15px rgba(6,182,212,0.4);">📱 Открыть Telegram Mini App (TMA)</a>
            <p>🕒 Время сервера: <b>{now_msk}</b> | Бот: <b>@MyAiGem_bot</b></p>
            
            <div class="modules">
                <div class="card">
                    <b>📱 Telegram Mini App</b><br><span style="color:#94a3b8">Живой мобильный пульт</span>
                </div>
                <div class="card">
                    <b>🌅 Утренний Дайджест</b><br><span style="color:#94a3b8">Ежедневно в 09:00 MSK</span>
                </div>
                <div class="card">
                    <b>🏠 Умный дом Яндекса</b><br><span style="color:#94a3b8">Свет, климат, сценарии</span>
                </div>
                <div class="card">
                    <b>🚗 Drive2.ru Монитор</b><br><span style="color:#94a3b8">ЛС, события (60с)</span>
                </div>
                <div class="card">
                    <b>🔵 VK Монитор</b><br><span style="color:#94a3b8">ЛС, заявки, алерты</span>
                </div>
                <div class="card">
                    <b>💬 MAX Монитор</b><br><span style="color:#94a3b8">web.max.ru (60с)</span>
                </div>
                <div class="card">
                    <b>🔢 Кредиты & Ипотека</b><br><span style="color:#94a3b8">Аннуитет, выгода досрочки</span>
                </div>
                <div class="card">
                    <b>😴 Калькулятор сна</b><br><span style="color:#94a3b8">90-мин фазы, Power Nap</span>
                </div>
                <div class="card">
                    <b>🌤 Погода & Осадки</b><br><span style="color:#94a3b8">Радар дождя по районам</span>
                </div>
            </div>

            <h2>⏰ Активные напоминания ({len(reminders)})</h2>
            <table>
                <thead>
                    <tr><th>#</th><th>Задача</th><th>Время срабатывания</th><th>ID</th></tr>
                </thead>
                <tbody>
                    {r_rows if r_rows else '<tr><td colspan="4">Напоминаний нет</td></tr>'}
                </tbody>
            </table>

            <h2>🎂 Дни рождения ({len(birthdays)})</h2>
            <table>
                <thead>
                    <tr><th>#</th><th>Имя</th><th>Дата</th><th>Возраст</th><th>Осталось</th><th>Заметка</th></tr>
                </thead>
                <tbody>
                    {b_rows if b_rows else '<tr><td colspan="6">Список пуст</td></tr>'}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
