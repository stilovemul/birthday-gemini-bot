import re
import html
import logging
from aiogram import types
from aiogram.enums import ParseMode

logger = logging.getLogger("CareerInterviewFormatter")


def clean_telegram_html(text: str) -> str:
    """
    Безопасно форматирует текст для отправки в Telegram с ParseMode.HTML:
    - Сохраняет легитимные теги Telegram (<b>, <i>, <code>, <u>, <s>, <pre>, <a>).
    - Экранирует случайные символы '<', '>', '&' (например, при сравнении чисел или операциях).
    - Преобразует Markdown-разметку (**bold**, `code`) в соответствующие HTML-теги.
    - Исключает отображение сырых тегов пользователю.
    """
    if not text:
        return ""

    s = str(text)

    # 1. Извлекаем блоки кода в токены
    code_blocks = []
    def _save_code(m):
        code_blocks.append(f"<code>{html.escape(m.group(1), quote=False)}</code>")
        return f"___CODE_BLOCK_{len(code_blocks)-1}___"
    
    s = re.sub(r"`([^`]+)`", _save_code, s)

    # 2. Извлекаем уже существующие допустимые теги Telegram
    valid_tags = []
    def _save_tag(m):
        valid_tags.append(m.group(0))
        return f"___VALID_TAG_{len(valid_tags)-1}___"

    tag_pattern = r"</?(?:b|strong|i|em|u|s|strike|del|code|pre)\b[^>]*>|<a\s+href=[\"'][^\"']*[\"']>[^<]*</a>"
    s = re.sub(tag_pattern, _save_tag, s, flags=re.IGNORECASE)

    # 3. Экранируем все остальные спецсимволы
    s = html.escape(s, quote=False)

    # 4. Преобразуем Markdown bold (**жирный**) в <b>...</b>
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

    # 5. Преобразуем Markdown курсив (*курсив* или _курсив_) в <i>...</i>
    s = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"<i>\1</i>", s)

    # 6. Возвращаем сохраненные допустимые теги и блоки кода
    for i, tag in enumerate(valid_tags):
        s = s.replace(f"___VALID_TAG_{i}___", tag)
    for i, code in enumerate(code_blocks):
        s = s.replace(f"___CODE_BLOCK_{i}___", code)

    return s


async def send_clean_html(target, text: str, reply_markup=None) -> types.Message:
    """
    Отправляет сообщение с ParseMode.HTML. Если Telegram возвращает ошибку
    парсинга разметки (TelegramBadRequest), отправляет очищенный текст без тегов.
    """
    cleaned = clean_telegram_html(text)
    
    if isinstance(target, types.CallbackQuery):
        send_fn = target.message.answer
    elif hasattr(target, "answer"):
        send_fn = target.answer
    elif hasattr(target, "message") and hasattr(target.message, "answer"):
        send_fn = target.message.answer
    else:
        raise ValueError(f"Неизвестный целевой объект для отправки: {type(target)}")

    try:
        return await send_fn(cleaned, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except Exception as e:
        logger.warning(f"Ошибка парсинга HTML в Telegram ({e}). Отправляю очищенный текст...")
        plain = re.sub(r"<[^>]+>", "", cleaned)
        return await send_fn(plain, reply_markup=reply_markup)
