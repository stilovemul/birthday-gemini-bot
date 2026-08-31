import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from modules.ai_deep_research.researcher import conduct_deep_research
from modules.ai_deep_research.fact_checker import verify_claim_or_news

logger = logging.getLogger("ResearchHandlers")
router = Router(name="ai_deep_research")


def format_research_card(data: dict) -> str:
    lines = [
        f"🔬 <b>{data.get('title')}</b>\n",
        f"💡 <b>Главный вывод (Summary):</b>\n<i>{data.get('executive_summary')}</i>\n",
        "📌 <b>Ключевые инсайты:</b>"
    ]
    for ins in data.get("key_insights", []):
        lines.append(f"  • {ins}")

    comp = data.get("comparison", [])
    if comp:
        lines.append("\n📊 <b>Сравнительный анализ вариантов:</b>")
        for it in comp:
            lines.append(
                f"  👉 <b>{it.get('name')}</b> (Рейтинг: <b>{it.get('score', '9/10')}</b>)\n"
                f"     + <i>{it.get('pros')}</i>\n"
                f"     - <i>{it.get('cons')}</i>"
            )

    if data.get("verdict"):
        lines.append(f"\n🎯 <b>Итоговая рекомендация:</b>\n{data['verdict']}")

    return "\n".join(lines)


def format_factcheck_card(data: dict) -> str:
    lines = [
        "🛡 <b>Результат фактчекинга и проверки новости:</b>\n",
        f"💬 <b>Тезис:</b> <i>«{data.get('claim')}»</i>\n",
        f"⚖️ <b>Вердикт:</b> <b>{data.get('verdict')}</b> (Точность: <b>{data.get('confidence')}%</b>)",
        f"📢 <b>Уровень кликбейта:</b> <i>{data.get('clickbait')}</i>\n",
        f"🔍 <b>Фактическая картина:</b>\n{data.get('real_facts')}\n"
    ]
    
    mans = data.get("manipulations", [])
    if mans:
        lines.append("⚠️ <b>Обнаруженные манипуляции:</b>")
        for m in mans:
            lines.append(f"  • {m}")

    return "\n".join(lines)


@router.message(Command("research"))
@router.message(F.text.startswith("🔬 Исследуй"))
@router.message(F.text.startswith("/research"))
async def cmd_research(message: types.Message):
    user_id = message.from_user.id
    topic = message.text.replace("/research", "").replace("🔬 Исследуй", "").strip()
    if not topic:
        topic = "Тренды зимних шин с шипами и липучки для СПб 2026: что надежнее и тише"

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await conduct_deep_research(user_id, topic)
    text = format_research_card(data)
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("factcheck"))
@router.message(Command("checknews"))
@router.message(F.text.startswith("🛡 Проверь новость"))
@router.message(F.text.startswith("/factcheck"))
async def cmd_factcheck(message: types.Message):
    user_id = message.from_user.id
    claim = message.text.replace("/factcheck", "").replace("/checknews", "").replace("🛡 Проверь новость", "").strip()
    if not claim:
        claim = "В РФ ввели обязательный налог на установку домашних кондиционеров и балконов с 1 сентября"

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await verify_claim_or_news(user_id, claim)
    text = format_factcheck_card(data)
    await message.answer(text, parse_mode=ParseMode.HTML)
