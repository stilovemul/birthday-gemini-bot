from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

WEBAPP_URL = "https://birthday-gemini-bot.onrender.com/app"

MAIN_MENU_BUTTONS = [
    "📱 Открыть Дашборд (App)",
    "🏠 Дом", "🌅 Дайджест", "🤖 Gemini AI", "🎨 Фото",
    "📬 Входящие", "🌤 Погода", "😴 Сон", "⏰ Напоминания",
    "🎂 Дни рожд.", "💳 Подписки", "🧩 Правила", "🍽 Еда",
    "🎁 Промо & PS", "🎬 Кино", "✨ Промпты", "✍️ Текст AI",
    "💬 Знакомства", "🕵️‍♂️ Тайный СПб", "🌲 Выходные", "📍 Рестораны",
    "🏕 Загород", "🎁 Подарки", "🎧 Музыка", "📸 Фото-Споты",
    "👨‍🍳 Шеф-Ужин", "🗣 Живой English"
]


def get_main_menu() -> ReplyKeyboardMarkup:
    """Returns ultra-compact 4-column multi-functional keyboard without items moved exclusively to Dashboard."""
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
            KeyboardButton(text="🌤 Погода"),
            KeyboardButton(text="😴 Сон"),
            KeyboardButton(text="⏰ Напоминания")
        ],
        [
            KeyboardButton(text="🎂 Дни рожд."),
            KeyboardButton(text="💳 Подписки"),
            KeyboardButton(text="🧩 Правила"),
            KeyboardButton(text="🍽 Еда")
        ],
        [
            KeyboardButton(text="🎁 Промо & PS"),
            KeyboardButton(text="🎬 Кино"),
            KeyboardButton(text="✨ Промпты"),
            KeyboardButton(text="✍️ Текст AI")
        ],
        [
            KeyboardButton(text="💬 Знакомства"),
            KeyboardButton(text="🕵️‍♂️ Тайный СПб"),
            KeyboardButton(text="🌲 Выходные"),
            KeyboardButton(text="📍 Рестораны")
        ],
        [
            KeyboardButton(text="🏕 Загород"),
            KeyboardButton(text="🎁 Подарки"),
            KeyboardButton(text="🎧 Музыка"),
            KeyboardButton(text="📸 Фото-Споты")
        ],
        [
            KeyboardButton(text="👨‍🍳 Шеф-Ужин"),
            KeyboardButton(text="🗣 Живой English")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=False)


def get_mode_keyboard(mode_title: str = "Режим диалога") -> ReplyKeyboardMarkup:
    """
    Returns sleek navigation buttons to replace the big menu while user is in active category mode:
    [ 🔙 Назад ]  [ 🏁 Главное меню ]
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔙 Назад"),
                KeyboardButton(text="🏁 Главное меню")
            ]
        ],
        resize_keyboard=True,
        is_persistent=False
    )


def is_back_command(text: str) -> bool:
    """Checks if the user sent a 'back / step back' command or button."""
    if not text:
        return False
    t = text.strip().lower()
    back_phrases = {
        "🔙 назад",
        "назад",
        "шаг назад",
        "на один шаг назад",
        "назад на один шаг",
        "вернуться назад",
        "вернуться",
        "вернись назад",
        "вернись",
        "назад в меню",
        "предыдущий шаг",
        "отмена",
        "отменить",
        "/back",
        "back"
    }
    return t in back_phrases


def is_exit_command(text: str) -> bool:
    """Checks if the user sent an explicit exit / back to menu command or button."""
    if not text:
        return False
    t = text.strip().lower()
    exit_phrases = {
        "🏁 закончить режим (главное меню)",
        "🏁 закончить режим",
        "закончить режим",
        "🏁 главное меню",
        "главное меню",
        "🚪 главное меню",
        "меню",
        "выход",
        "выйти",
        "/stop",
        "/exit",
        "/cancel",
        "/menu"
    }
    return t in exit_phrases


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
