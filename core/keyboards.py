from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Returns main multi-functional keyboard."""
    kb = [
        [
            KeyboardButton(text="🤖 Gemini AI"),
            KeyboardButton(text="🎨 Генерация картинок")
        ],
        [
            KeyboardButton(text="🥗 Сканер еды & КБЖУ"),
            KeyboardButton(text="🚗 Drive2 Уведомления")
        ],
        [
            KeyboardButton(text="⏰ Напоминания"),
            KeyboardButton(text="🎂 Дни рождения")
        ],
        [
            KeyboardButton(text="📝 Заметки"),
            KeyboardButton(text="❓ Справка")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)


def get_birthday_submenu() -> ReplyKeyboardMarkup:
    """Submenu for birthdays."""
    kb = [
        [
            KeyboardButton(text="🎂 Сегодня"),
            KeyboardButton(text="📅 Ближайшие ДР")
        ],
        [
            KeyboardButton(text="📋 Все дни рождения"),
            KeyboardButton(text="➕ Как добавить")
        ],
        [
            KeyboardButton(text="🔙 Главное меню")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)
