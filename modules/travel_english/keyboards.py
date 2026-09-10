"""
Клавиатуры для модуля «🗣 Живой English (Travel & Street Smart)»:
- Инлайн-меню режимов, каталогов сценариев, категорий проверочных квизов и шпаргалок.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from modules.travel_english.scenarios_catalog import SCENARIOS
from modules.travel_english.quizzes_catalog import QUIZ_CATEGORIES
from modules.travel_english.cheat_sheets import CHEAT_SHEETS


def get_travel_english_main_keyboard() -> InlineKeyboardMarkup:
    """Главное интерактивное меню модуля английского языка."""
    kb = [
        [
            InlineKeyboardButton(text="🎭 Ролевой диалог с иностранцем", callback_data="eng_menu_scenarios")
        ],
        [
            InlineKeyboardButton(text="📝 Проверочный Квиз (Тест)", callback_data="eng_menu_quizzes"),
            InlineKeyboardButton(text="⚡️ Перевод на сленг", callback_data="eng_menu_instant")
        ],
        [
            InlineKeyboardButton(text="📋 Золотые шпаргалки", callback_data="eng_menu_cheats"),
            InlineKeyboardButton(text="📊 Мой уровень & XP", callback_data="eng_menu_profile")
        ],
        [
            InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_scenarios_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора бытовых ситуаций для ролевой игры."""
    kb = []
    sc_items = list(SCENARIOS.items())
    for i in range(0, len(sc_items), 2):
        row = []
        for key, data in sc_items[i:i+2]:
            row.append(InlineKeyboardButton(
                text=f"{data['title']}",
                callback_data=f"eng_sc_{key}"
            ))
        kb.append(row)

    kb.append([
        InlineKeyboardButton(text="🔙 Назад в меню английского", callback_data="eng_main_menu"),
        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_dialog_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура быстрых действий внутри активного ролевого диалога."""
    kb = [
        [
            InlineKeyboardButton(text="💡 Подскажи, что ответить", callback_data="eng_action_suggest"),
            InlineKeyboardButton(text="🔄 Другая ситуация", callback_data="eng_menu_scenarios")
        ],
        [
            InlineKeyboardButton(text="📝 Пройти квиз", callback_data="eng_menu_quizzes"),
            InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_quiz_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора категории проверочной работы / квиза."""
    kb = [
        [
            InlineKeyboardButton(text="⚡️ Экспресс-Блиц (5 вопросов)", callback_data="eng_start_quiz_blitz")
        ],
        [
            InlineKeyboardButton(text="🍻 Бар & Еда", callback_data="eng_start_quiz_food_bar"),
            InlineKeyboardButton(text="✈️ Аэропорт & Отель", callback_data="eng_start_quiz_travel_airport")
        ],
        [
            InlineKeyboardButton(text="🕶 Уличный сленг нейтивов", callback_data="eng_start_quiz_slang_idioms")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в меню английского", callback_data="eng_main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_quiz_options_keyboard(qid: str, options: list) -> InlineKeyboardMarkup:
    """Клавиатура с 4 вариантами ответов на вопрос квиза."""
    letters = ["🅰️", "🅱️", "🅲", "🅳"]
    kb = []
    for idx, opt in enumerate(options):
        letter = letters[idx] if idx < len(letters) else f"#{idx+1}"
        # Делаем короткий лейбл кнопки
        short_opt = opt if len(opt) <= 25 else opt[:23] + "..."
        kb.append([
            InlineKeyboardButton(
                text=f"{letter} {short_opt}",
                callback_data=f"eng_ans_{qid}_{idx}"
            )
        ])

    kb.append([
        InlineKeyboardButton(text="🔄 Другой вопрос", callback_data="eng_next_quiz_blitz"),
        InlineKeyboardButton(text="🔙 Меню тестов", callback_data="eng_menu_quizzes")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_quiz_result_keyboard(category: str) -> InlineKeyboardMarkup:
    """Клавиатура после показа разбора ответа на вопрос."""
    kb = [
        [
            InlineKeyboardButton(text="➡️ Следующий вопрос (+10 XP)", callback_data=f"eng_next_quiz_{category}"),
            InlineKeyboardButton(text="🎭 В ролевой диалог", callback_data="eng_menu_scenarios")
        ],
        [
            InlineKeyboardButton(text="📊 Мой уровень & XP", callback_data="eng_menu_profile"),
            InlineKeyboardButton(text="🔙 Меню тестов", callback_data="eng_menu_quizzes")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_cheat_sheets_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора золотой шпаргалки."""
    kb = [
        [
            InlineKeyboardButton(text="☕️ Кафе, Бар & Ресторан", callback_data="eng_cs_food_drink"),
            InlineKeyboardButton(text="✈️ Аэропорт & Самолет", callback_data="eng_cs_airport_flight")
        ],
        [
            InlineKeyboardButton(text="🏨 Отель, Заезд & Быт", callback_data="eng_cs_hotel_airbnb"),
            InlineKeyboardButton(text="🚕 Такси, Улица & Торг", callback_data="eng_cs_street_taxi")
        ],
        [
            InlineKeyboardButton(text="🕶 ТОП-10 фраз нейтивов", callback_data="eng_cs_native_slang")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в меню английского", callback_data="eng_main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
