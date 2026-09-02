import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
from modules.prompt_studio.generator import generate_super_prompt, AI_TARGET_MODELS

logger = logging.getLogger("PromptStudioHandlers")
router = Router(name="prompt_studio")


def get_prompt_models_keyboard(current_model: str = "chatgpt") -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🤖 ChatGPT" + (" ✅" if current_model == "chatgpt" else ""), callback_data="ps_set_chatgpt"),
            InlineKeyboardButton(text="🧠 Claude 3.5" + (" ✅" if current_model == "claude" else ""), callback_data="ps_set_claude")
        ],
        [
            InlineKeyboardButton(text="🎨 Midjourney" + (" ✅" if current_model == "midjourney" else ""), callback_data="ps_set_midjourney"),
            InlineKeyboardButton(text="🖼 Flux / SD" + (" ✅" if current_model == "flux_sd" else ""), callback_data="ps_set_flux_sd")
        ],
        [
            InlineKeyboardButton(text="💎 Gemini Pro" + (" ✅" if current_model == "gemini" else ""), callback_data="ps_set_gemini"),
            InlineKeyboardButton(text="⚡️ DeepSeek R1" + (" ✅" if current_model == "deepseek" else ""), callback_data="ps_set_deepseek")
        ],
        [
            InlineKeyboardButton(text="🎬 Sora & Video AI" + (" ✅" if current_model == "video_ai" else ""), callback_data="ps_set_video_ai")
        ],
        [
            InlineKeyboardButton(text="🔄 Сменить задачу", callback_data="ps_new_task"),
            InlineKeyboardButton(text="🚪 Выйти", callback_data="mode_exit_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("prompts"))
@router.message(Command("prompt"))
@router.message(F.text.in_(["✨ Промпты", "✨ Генератор промптов", "Промпты", "Генератор промптов"]))
async def cmd_prompt_studio(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.prompt_studio_mode)
    await state.update_data(target_ai="chatgpt")
    
    text = (
        "✨ <b>Prompt Engineering Studio — Генератор промптов для нейросетей:</b>\n\n"
        "Выберите целевую нейросеть кнопками ниже и <b>напишите вашу задачу простыми словами</b> "
        "(например: <i>«напиши продающий пост для Telegram»</i>, <i>«киберпанк город под дождем»</i>, <i>«скрипт парсера на Python»</i>).\n\n"
        "🎯 <b>Текущая модель:</b> 🤖 <b>ChatGPT / GPT-4o</b>\n"
        "💡 Я сформирую профессиональный, структурированный промпт с максимальным качеством генерации!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_prompt_models_keyboard("chatgpt"))


@router.callback_query(F.data.startswith("ps_set_"))
async def cb_set_prompt_model(callback: types.CallbackQuery, state: FSMContext):
    model_key = callback.data.replace("ps_set_", "")
    await state.set_state(ActiveModeStates.prompt_studio_mode)
    await state.update_data(target_ai=model_key)
    
    model_info = AI_TARGET_MODELS.get(model_key, AI_TARGET_MODELS["chatgpt"])
    await callback.message.edit_text(
        f"🎯 <b>Выбрана нейросеть:</b> {model_info['title']}\n"
        f"📝 <i>{model_info['description']}</i>\n\n"
        "💬 <b>Напишите задачу или идею</b> — я сгенерирую идеальный промпт для этой модели:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_prompt_models_keyboard(model_key)
    )
    await callback.answer(f"Выбрана: {model_info['title']}")


@router.callback_query(F.data == "ps_new_task")
async def cb_new_task(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.prompt_studio_mode)
    data = await state.get_data()
    current_model = data.get("target_ai", "chatgpt")
    model_info = AI_TARGET_MODELS.get(current_model, AI_TARGET_MODELS["chatgpt"])
    
    await callback.message.answer(
        f"💬 <b>Напишите новую задачу для {model_info['title']}:</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(ActiveModeStates.prompt_studio_mode, F.text)
async def handle_prompt_studio_input(message: types.Message, state: FSMContext):
    user_text = message.text.strip()
    if user_text.startswith("/") or user_text in ["🚪 Главное меню", "Главное меню", "Выход"]:
        await state.clear()
        return

    data = await state.get_data()
    target_ai = data.get("target_ai", "chatgpt")

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    result = await generate_super_prompt(message.from_user.id, user_text, target_ai)

    opt_prompt = html.escape(result.get("optimized_prompt", ""))
    explanation = html.escape(result.get("explanation", ""))
    settings = html.escape(result.get("recommended_settings", ""))
    pro_tip = html.escape(result.get("pro_tip", ""))
    ai_title = html.escape(result.get("target_ai", "ИИ"))

    card = (
        f"✨ <b>Готовый промпт для {ai_title}:</b>\n\n"
        f"📋 <b>Скопируйте и отправьте в нейросеть:</b>\n"
        f"<code>{opt_prompt}</code>\n\n"
        f"🔍 <b>Архитектура промпта:</b>\n<i>{explanation}</i>\n\n"
        f"⚙️ <b>Параметры:</b> <code>{settings}</code>\n"
        f"💡 <b>Pro-Tip:</b> <i>{pro_tip}</i>"
    )
    await message.answer(card, parse_mode=ParseMode.HTML, reply_markup=get_prompt_models_keyboard(target_ai))
