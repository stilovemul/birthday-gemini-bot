from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

WEBAPP_URL = "https://birthday-gemini-bot.onrender.com/app"


def get_main_menu() -> ReplyKeyboardMarkup:
    """Returns ultra-compact 4-column multi-functional keyboard."""
    kb = [
        [
            KeyboardButton(text="📱 Открыть Дашборд (App)", web_app=WebAppInfo(url=WEBAPP_URL))
        ],
        [
            KeyboardButton(text="🏠 Дом"),
            KeyboardButton(text="🌅 Дайджест"),
            KeyboardButton(text="🤖 Gemini AI"),
            KeyboardButton(text="🎨 Фото")
        ],
        [
            KeyboardButton(text="📬 Входящие"),
            KeyboardButton(text="🥗 КБЖУ"),
            KeyboardButton(text="🌤 Погода"),
            KeyboardButton(text="😴 Сон")
        ],
        [
            KeyboardButton(text="🔢 Кредиты"),
            KeyboardButton(text="🔐 Сейф"),
            KeyboardButton(text="⏰ Напоминания"),
            KeyboardButton(text="🎂 Дни рожд.")
        ],
        [
            KeyboardButton(text="📝 Заметки"),
            KeyboardButton(text="💳 Подписки"),
            KeyboardButton(text="🧩 Правила"),
            KeyboardButton(text="🍽 Еда")
        ],
        [
            KeyboardButton(text="🎁 Промо & PS"),
            KeyboardButton(text="🚗 Авто-Юрист"),
            KeyboardButton(text="🔬 Ресерч"),
            KeyboardButton(text="📵 Антиспам")
        ],
        [
            KeyboardButton(text="❓ Справка")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=False)


def get_mode_keyboard(mode_title: str = "Режим диалога") -> ReplyKeyboardMarkup:
    """
    Returns a sleek single-button keyboard to replace the big menu while user is in active category mode.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏁 Закончить режим (Главное меню)")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )


def get_birthday_submenu() -> ReplyKeyboardMarkup:
    """Returns birthday management submenu keyboard."""
    kb = [
        [KeyboardButton(text="➕ Добавить день рождения"), KeyboardButton(text="📋 Список всех ДР")],
        [KeyboardButton(text="🔍 Поиск ДР"), KeyboardButton(text="🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=False)


def get_notes_keyboard() -> ReplyKeyboardMarkup:
    """Returns notes management keyboard."""
    kb = [
        [KeyboardButton(text="➕ Новая заметка"), KeyboardButton(text="📋 Все заметки")],
        [KeyboardButton(text="🔙 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=False)


def get_webapp_inline_keyboard() -> InlineKeyboardMarkup:
    """Returns inline button to launch the WebApp dashboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Открыть интерактивный Дашборд",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ]
    )
