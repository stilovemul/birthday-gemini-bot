from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

WEBAPP_URL = "https://birthday-gemini-bot.onrender.com/app"


def get_main_menu() -> ReplyKeyboardMarkup:
    """Returns main multi-functional keyboard with collapsible layout."""
    kb = [
        [
            KeyboardButton(text="📱 Открыть Дашборд (App)", web_app=WebAppInfo(url=WEBAPP_URL))
        ],
        [
            KeyboardButton(text="🏠 Умный дом"),
            KeyboardButton(text="🌅 Утренний дайджест")
        ],
        [
            KeyboardButton(text="🤖 Gemini AI"),
            KeyboardButton(text="🎨 Генерация картинок")
        ],
        [
            KeyboardButton(text="🚗 Drive2 Уведомления"),
            KeyboardButton(text="🔵 VK Уведомления"),
            KeyboardButton(text="💬 MAX Уведомления")
        ],
        [
            KeyboardButton(text="🥗 Сканер еды & КБЖУ"),
            KeyboardButton(text="🌤 Погода & Осадки")
        ],
        [
            KeyboardButton(text="😴 Калькулятор сна"),
            KeyboardButton(text="🔢 Калькулятор кредитов")
        ],
        [
            KeyboardButton(text="🔐 Секретный сейф"),
            KeyboardButton(text="⏰ Напоминания")
        ],
        [
            KeyboardButton(text="🎂 Дни рождения"),
            KeyboardButton(text="📝 Заметки")
        ],
        [
            KeyboardButton(text="💳 Подписки"),
            KeyboardButton(text="🧩 Мои правила")
        ],
        [
            KeyboardButton(text="🍽 Еда"),
            KeyboardButton(text="🎁 Промокоды & 🎮 Игры")
        ],
        [
            KeyboardButton(text="🚗 Авто-Юрист & 🚨 ДТП"),
            KeyboardButton(text="🔬 Deep Research & 🛡 Фактчек")
        ],
        [
            KeyboardButton(text="📵 Проверить номер"),
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
