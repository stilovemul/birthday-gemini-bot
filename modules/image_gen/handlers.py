import re
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from core.keyboards import get_main_menu
from modules.image_gen.generator import generate_image_bytes

router = Router(name="image_gen")


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
            "• <code>/image неоновый кот в очках киберпанк</code>\n"
            "• <code>/draw спорткар будущего на фоне заката</code>\n"
            "• <code>/art уютный домик в заснеженном лесу, 4k, акварель</code>\n\n"
            "Или просто напишите в чат: <i>«Нарисуй космический корабль»</i>"
        )
        await message.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    status_msg = await message.answer("🎨 <i>Генерирую изображение через нейросеть Flux... (обычно 5-10 сек)</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    success, img_bytes, prompt_res = await generate_image_bytes(prompt)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if success and img_bytes:
        photo_file = BufferedInputFile(img_bytes, filename="generated.jpg")
        caption = f"✨ <b>Результат по запросу:</b>\n«<i>{prompt_res}</i>»"
        await message.answer_photo(photo_file, caption=caption, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
    else:
        await message.answer(f"❌ {prompt_res}", reply_markup=get_main_menu())


@router.message(F.text == "🎨 Генерация картинок")
async def cmd_image_button(message: types.Message):
    text = (
        "🎨 <b>Генератор изображений через нейросеть Flux</b>\n\n"
        "Отправьте команду <code>/image</code> с любым описанием, например:\n\n"
        "• <code>/image футуристичный спорткар на улицах Токио</code>\n"
        "• <code>/image милый щенок корги в космосе, digital art</code>\n"
        "• <code>/image логотип кофейни с чашкой и паром, минимализм</code>\n\n"
        "Также можно просто написать боту: <i>«Нарисуй красивый водопад в горах»</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
