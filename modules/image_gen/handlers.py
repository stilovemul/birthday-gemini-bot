import re
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.image_gen.generator import (
    generate_image_bytes,
    get_last_image_info,
    set_user_awaiting_image,
    set_user_engine,
    get_user_engine,
    refine_prompt_with_ai,
    start_image_session,
    update_image_session,
    end_image_session,
    is_in_image_session,
    get_image_session
)

router = Router(name="image_gen")


def get_image_action_keyboard() -> InlineKeyboardMarkup:
    """Returns inline keyboard under generated images with finish button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Максимальный реализм", callback_data="img_make_realistic"),
                InlineKeyboardButton(text="🔄 Другой вариант", callback_data="img_redraw")
            ],
            [
                InlineKeyboardButton(text="⏹ Закончить генерацию", callback_data="img_finish_session")
            ]
        ]
    )


def get_engine_selection_keyboard(current_engine: str = "realvis") -> InlineKeyboardMarkup:
    """Returns inline keyboard for selecting AI image generation model."""
    btn_flux = "✅ 📸 Фотореализм (RealVisXL)" if current_engine == "realvis" or "real" in current_engine else "📸 Фотореализм (RealVisXL)"
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
            "Выберите движок/стиль ниже и <b>просто напишите в чат описание</b> того, что нужно нарисовать:\n\n"
            "• <i>«Русская девушка в постели утром, реальное фото»</i>\n"
            "• <i>«Спорткар будущего на фоне ночного города»</i>\n"
            "• <i>«Милый пушистый кот в очках»</i>\n\n"
            "👇 <i>Выберите стиль или отправьте текст:</i>"
        )
        await message.answer(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_engine_selection_keyboard(curr_engine)
        )
        return

    status_msg = await message.answer("🎨 <i>Генерирую фотореалистичное изображение... (3-6 сек)</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    success, img_bytes, orig_p, en_p = await generate_image_bytes(prompt, user_id=user_id)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if success and img_bytes:
        start_image_session(user_id, orig_p, en_p)
        photo_file = BufferedInputFile(img_bytes, filename="generated.jpg")
        caption = (
            f"✨ <b>Запрос:</b> «<i>{orig_p}</i>»\n\n"
            "💡 <b>Режим редактирования активен:</b> пишите любые изменения прямо в чат (например: <i>«давай блондинку»</i>, <i>«одеяло ниже спусти»</i>).\n"
            "Для выхода нажмите <b>«⏹ Закончить генерацию»</b>."
        )
        await message.answer_photo(
            photo_file,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_image_action_keyboard()
        )
    else:
        await message.answer(f"❌ {en_p}", reply_markup=get_main_menu())


@router.callback_query(F.data == "img_finish_session")
async def callback_finish_image_session(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    end_image_session(user_id)
    await callback.answer("Сессия генерации завершена!")
    await callback.message.answer(
        "✅ <b>Генерация завершена!</b> Картинка зафиксирована.\n\n"
        "Бот вернулся в обычный режим. Чем могу помочь?",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data.startswith("engine_"))
async def callback_set_engine(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    code = callback.data.replace("engine_", "")
    engine_map = {
        "flux": ("realvis", "📸 Фотореализм (RealVisXL)"),
        "turbo": ("turbo", "⚡ Nano / Turbo"),
        "anime": ("flux-anime", "🎨 Anime & Art"),
        "3d": ("flux-3d", "🌌 3D Render")
    }
    
    eng_val, eng_name = engine_map.get(code, ("realvis", "📸 Фотореализм (RealVisXL)"))
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
    sess = get_image_session(user_id)
    last_prompt = sess["current_en_prompt"] if sess else None
    
    if not last_prompt:
        await callback.answer("Сессия устарела. Напишите новое описание!", show_alert=True)
        return

    await callback.answer("Усиливаю фотореализм...")
    status_msg = await callback.message.answer("📸 <i>Усиливаю фотореализм и текстуру кожи...</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_PHOTO)

    refined_prompt = await refine_prompt_with_ai(last_prompt, "maximum photorealism, authentic raw 35mm film photograph, highly detailed human skin texture, pores, soft natural lighting")
    success, img_bytes, orig_p, _ = await generate_image_bytes(refined_prompt, user_id=user_id, is_already_en=True, force_engine="realvis")

    try:
        await status_msg.delete()
    except Exception:
        pass

    if success and img_bytes:
        update_image_session(user_id, "Максимальный фотореализм", refined_prompt)
        photo_file = BufferedInputFile(img_bytes, filename="realism.jpg")
        caption = (
            "📸 <b>Максимальный фотореализм!</b>\n\n"
            "💡 <i>Пишите любые дальнейшие правки текстом или завершите кнопкой ниже:</i>"
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
    sess = get_image_session(user_id)
    last_prompt = sess["current_en_prompt"] if sess else None
    
    if not last_prompt:
        await callback.answer("Сессия устарела. Напишите новое описание!", show_alert=True)
        return

    await callback.answer("Генерирую новый вариант...")
    status_msg = await callback.message.answer("🔄 <i>Генерирую новый вариант ракурса и кадра...</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_PHOTO)

    success, img_bytes, orig_p, _ = await generate_image_bytes(last_prompt, user_id=user_id, is_already_en=True)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if success and img_bytes:
        photo_file = BufferedInputFile(img_bytes, filename="redraw.jpg")
        caption = (
            "🔄 <b>Новый вариант готов!</b>\n\n"
            "💡 <i>Пишите любые дальнейшие пожелания или завершите кнопкой ниже:</i>"
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
