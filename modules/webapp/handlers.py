from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from core.keyboards import get_webapp_inline_keyboard

router = Router()

@router.message(Command("app"))
@router.message(F.text.lower().in_(["📱 открыть дашборд (app)", "📱 открыть дашборд", "дашборд", "mini app", "открыть приложение", "веб апп"]))
async def cmd_open_webapp(message: Message):
    await message.answer(
        "📱 <b>Интерактивный Telegram Mini App Дашборд:</b>\n\n"
        "• 🏠 <b>Умный дом:</b> живые тумблеры света, вытяжки, теплого пола и датчики.\n"
        "• 🌤 <b>Погода и климат:</b> точный радар и прогноз Приморского р-на.\n"
        "• 🎂 <b>Дни рождения:</b> обратный отсчет и быстрое добавление.\n"
        "• 🥗 <b>КБЖУ & Питание:</b> прогресс-бары калорий и лог приемов пищи.\n"
        "• 🔢 <b>Кредитный симулятор:</b> расчет экономии при досрочном погашении.\n\n"
        "👇 <i>Нажмите кнопку ниже, чтобы открыть приложение прямо в Telegram:</i>",
        reply_markup=get_webapp_inline_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    """
    Catches data sent via Telegram.WebApp.sendData() from the Mini App.
    """
    raw_data = (message.web_app_data.data or "").strip()
    if not raw_data:
        return
    # Import router dispatch handler logic or answer
    from modules.webapp.router import api_dispatch_command, DispatchCommandRequest
    await api_dispatch_command(DispatchCommandRequest(command=raw_data, user_id=message.from_user.id))

