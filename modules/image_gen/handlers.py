import re
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.image_gen.generator import (
    generate_image_bytes,
    get_last_image_info,
    set_last_image_prompt,
    set_user_awaiting_image,
    set_user_engine,
    get_user_engine,
    refine_prompt_with_ai
)

router = Router(name="image_gen")


def get_image_action_keyboard() -> InlineKeyboardMarkup:
    """Returns inline keyboard under generated images."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Сделать максимальный реализм", callback_data="img_make_realistic")
            ],
            [
                InlineKeyboardButton(text="🔄 Сгенерировать другой вариант", callback_data="img_redraw")
            ]
        ]
    )


def get_engine_selection_keyboard(current_engine: str = "flux-realism") -> InlineKeyboardMarkup:
    """Returns inline keyboard for selecting AI image generation model."""
    btn_flux = "✅ 📸 Фотореализм (Flux)" if "realism" in current_engine or current_engine == "flux" else "📸 Фотореализм (Flux)"
    btn_turbo = "✅ ⚡ Nano / Turbo" if current_engine == "turbo" else "⚡ Nano / Turbo"
    btn_anime = "✅ 🎨 Anime & Art" if current_engine == "flux-anime" else "🎨 Anime & Art"
    btn_3d = "✅ 🌌 3D Render" if current_engine == "flux-3d" else "🌌 3D Render"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=btn_flux, callback_data="engine_flux"),
                InlineKeyboardButton(text=btn_turbo, callback_data="engine_turbo")
            ],
            [
                InlineKeyboardButton(text=btn_anime, callback_data="engine_anime"),
                InlineKeyboardButton(text=btn_3d, callback_data="engine_3d")
            ]
        ]
    )


@router.message(Command("image"))
@router.message(Command("draw"))
@router.message(Command("art"))
async def cmd_generate_image(message: types.Message, bot: Bot):
    text = (message.text or "").strip()
    prompt = re.sub(r"^/(?:image|draw|art)\s*", "", text, flags=re.IGNORECASE).strip()
    user_id = message.from_user.id
    
    if not prompt:
        set_user_awaiting_image(user_id, True)
        curr_engine = get_user_engine(user_id)
        help_text = (
            "🎨 <b>Режим генерации картинок активен!</b>\n\n"
            "Выберите желаемый движок/стиль ниже и <b>просто напишите в чат описание</b> того, что нужно нарисовать:\n\n"
            "• <i>«Русская девушка в постели утром, реальное фото»</i>\n"
            "• <i>«Спорткар будущего на фоне ночного города»</i>\n"
            "• <i>«Милый пушистый кот в очках»</i>\n\n"
            "👇 <i>Выберите стиль или сразу отправьте текст:</i>"
        )
        await message.answer(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_engine_selection_keyboard(curr_engine)
        )
        return

    status_msg = await message.answer("🎨 <i>Генерирую фотореалистичное изображение... (5-10 сек)</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    success, img_bytes, orig_p, en_p = await generate_image_bytes(prompt, user_id=user_id)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if success and img_bytes:
        photo_file = BufferedInputFile(img_bytes, filename="generated.jpg")
        caption = (
            f"✨ <b>Запрос:</b> «<i>{orig_p}</i>»\n\n"
            "💡 <i>Если результат нужно изменить — напишите замечание (например: «Сделай лицо крупнее» или «Смени фон»).</i>"
        )
        await message.answer_photo(
            photo_file,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_image_action_keyboard()
        )
    else:
        await message.answer(f"❌ {en_p}", reply_markup=get_main_menu())


@router.callback_query(F.data.startswith("engine_"))
async def callback_set_engine(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    code = callback.data.replace("engine_", "")
    engine_map = {
        "flux": ("flux-realism", "📸 Фотореализм (Flux)"),
        "turbo": ("turbo", "⚡ Nano / Turbo"),
        "anime": ("flux-anime", "🎨 Anime & Art"),
        "3d": ("flux-3d", "🌌 3D Render")
    }
    
    eng_val, eng_name = engine_map.get(code, ("flux-realism", "📸 Фотореализм (Flux)"))
    set_user_engine(user_id, eng_val)
    set_user_awaiting_image(user_id, True)

    await callback.answer(f"Выбран стиль: {eng_name}")
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_engine_selection_keyboard(eng_val)
        )
    except Exception:
        pass


@router.callback_query(F.data == "img_make_realistic")
async def callback_make_realistic(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    info = get_last_image_info(user_id)
    if not info:
        await callback.answer("Предыдущий запрос устарел.", show_alert=True)
        return

    last_prompt = info["prompt"]
    await callback.answer("Перерисовываю в максимальном фотореализме...")
    status_msg = await callback.message.answer(f"📸 <i>Усиливаю фотореализм и убираю глянец для «{last_prompt}»...</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_PHOTO)

    refined_prompt = await refine_prompt_with_ai(last_prompt, "максимальный фотореализм, настоящее живое фото с реальной текстурой кожи, порами, естественным светом, без 3D, без кукольности, без глянца")
    success, img_bytes, orig_p, _ = await generate_image_bytes(refined_prompt, user_id=user_id, force_engine="flux-realism")

    try:
        await status_msg.delete()
    except Exception:
        pass

    if success and img_bytes:
        photo_file = BufferedInputFile(img_bytes, filename="realism.jpg")
        caption = (
            f"📸 <b>Максимальный фотореализм:</b> «<i>{orig_p}</i>»\n\n"
            "💡 <i>Напишите любые пожелания, если хотите что-то скорректировать!</i>"
        )
        await callback.message.answer_photo(
            photo_file,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_image_action_keyboard()
        )
    else:
        await callback.message.answer("❌ Не удалось перерисовать.")


@router.callback_query(F.data == "img_redraw")
async def callback_redraw_image(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    info = get_last_image_info(user_id)
    if not info:
        await callback.answer("Предыдущий запрос устарел. Напишите описание картинки!", show_alert=True)
        return

    last_prompt = info["prompt"]
    await callback.answer("Генерирую новый вариант...")
    status_msg = await callback.message.answer(f"🎨 <i>Перерисовываю «{last_prompt}» в новом варианте...</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_PHOTO)

    success, img_bytes, orig_p, _ = await generate_image_bytes(last_prompt, user_id=user_id)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if success and img_bytes:
        photo_file = BufferedInputFile(img_bytes, filename="redraw.jpg")
        caption = (
            f"🔄 <b>Новый вариант:</b> «<i>{orig_p}</i>»\n\n"
            "💡 <i>Напишите любые пожелания, если хотите что-то изменить!</i>"
        )
        await callback.message.answer_photo(
            photo_file,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_image_action_keyboard()
        )
    else:
        await callback.message.answer("❌ Не удалось сгенерировать повторный вариант.")


@router.message(F.text == "🎨 Генерация картинок")
async def cmd_image_button(message: types.Message):
    user_id = message.from_user.id
    set_user_awaiting_image(user_id, True)
    curr_engine = get_user_engine(user_id)
    
    text = (
        "🎨 <b>Режим генерации картинок активен!</b>\n\n"
        "Выберите движок/стиль ниже и <b>просто напишите в ответ, что нарисовать</b>:\n\n"
        "• <i>«Русская девушка в постели утром, реальное фото»</i>\n"
        "• <i>«Спорткар будущего на улицах ночного города»</i>\n"
        "• <i>«Милый щенок корги в космосе»</i>\n\n"
        "👇 <i>Отправьте текст картинки:</i>"
    )
    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_engine_selection_keyboard(curr_engine)
    )
