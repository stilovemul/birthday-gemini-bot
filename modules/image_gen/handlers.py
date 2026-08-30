import re
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.image_gen.generator import (
    generate_image_bytes,
    get_last_image_info,
    set_last_image_prompt
)

router = Router(name="image_gen")


def get_image_action_keyboard() -> InlineKeyboardMarkup:
    """Returns inline keyboard under generated images."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Сгенерировать другой вариант", callback_data="img_redraw")
            ]
        ]
    )


@router.message(Command("image"))
@router.message(Command("draw"))
@router.message(Command("art"))
async def cmd_generate_image(message: types.Message, bot: Bot):
    text = (message.text or "").strip()
    prompt = re.sub(r"^/(?:image|draw|art)\s*", "", text, flags=re.IGNORECASE).strip()
    
    if not prompt:
        help_text = (
            "🎨 <b>Генерация картинок по описанию:</b>\n\n"
            "Напишите команду и опишите то, что хотите увидеть:\n\n"
            "• <code>/image красивая русская девушка, реалистичное портретное фото</code>\n"
            "• <code>/draw спорткар будущего на фоне заката</code>\n"
            "• <code>/art уютный домик в заснеженном лесу, 4k, акварель</code>\n\n"
            "Или просто напишите в чат: <i>«Нарисуй русскую девушку в парке»</i>\n\n"
            "💡 <i>Если результат нужно изменить — просто напишите: «Тут нет девушки, сделай портрет крупным планом»</i>"
        )
        await message.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    status_msg = await message.answer("🎨 <i>Генерирую изображение через нейросеть Flux... (5-10 сек)</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    success, img_bytes, orig_p, en_p = await generate_image_bytes(prompt, user_id=message.from_user.id)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if success and img_bytes:
        photo_file = BufferedInputFile(img_bytes, filename="generated.jpg")
        caption = (
            f"✨ <b>Запрос:</b> «<i>{orig_p}</i>»\n\n"
            "💡 <i>Не понравилось? Напишите правки (например: «Сделай крупный план лица» или «Тут нет человека, добавь девушку»).</i>"
        )
        await message.answer_photo(
            photo_file,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_image_action_keyboard()
        )
    else:
        await message.answer(f"❌ {en_p}", reply_markup=get_main_menu())


@router.callback_query(F.data == "img_redraw")
async def callback_redraw_image(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    info = get_last_image_info(user_id)
    if not info:
        await callback.answer("Предыдущий запрос устарел. Напишите: /image <описание>", show_alert=True)
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
    text = (
        "🎨 <b>Генератор изображений через нейросеть Flux</b>\n\n"
        "Отправьте команду <code>/image</code> с любым описанием, например:\n\n"
        "• <code>/image красивая русская девушка, реалистичное фото на природе</code>\n"
        "• <code>/image футуристичный спорткар на улицах Токио</code>\n"
        "• <code>/image милый щенок корги в космосе, digital art</code>\n\n"
        "Также можно просто написать боту: <i>«Нарисуй девушку в зимнем пальто»</i>\n\n"
        "✨ <b>Доработка:</b> Если в картинке чего-то не хватает, просто напишите: <i>«Тут нет девушки, добавь её крупным планом»</i>!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
