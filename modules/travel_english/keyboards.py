"""
Клавиатуры для модуля «🗣 Живой English (Travel & Street Smart)»:
- Инлайн-меню режимов, каталогов сценариев, категорий проверочных квизов и шпаргалок.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from modules.travel_english.scenarios_catalog import SCENARIOS
from modules.travel_english.quizzes_catalog import QUIZ_CATEGORIES
from modules.travel_english.cheat_sheets import CHEAT_SHEETS
from modules.travel_english.storage import get_saved_dialog, get_all_saved_dialogs


def get_travel_english_main_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """Главное интерактивное меню модуля английского языка с кнопкой продолжения диалога."""
    kb = []

    # Проверяем, есть ли у пользователя сохраненный диалог
    saved = get_saved_dialog(user_id) if user_id else None
    if saved and saved.get("turns", 0) > 0:
        sc_key = saved.get("scenario_key", "bar_dating")
        sc_info = SCENARIOS.get(sc_key, {})
        char_name = sc_info.get("character", "Собеседник")
        icon = sc_info.get("icon", "💬")
        turns = saved.get("turns", 1)

        kb.append([
            InlineKeyboardButton(
                text=f"⏯ Продолжить диалог: {icon} {char_name} (Раунд {turns})",
                callback_data=f"eng_resume_{sc_key}"
            )
        ])
        kb.append([
            InlineKeyboardButton(text="✍️ Задать свою ситуацию (Магазин, Авто...)", callback_data="eng_create_custom")
        ])
        kb.append([
            InlineKeyboardButton(text="🍸 Новое знакомство в баре (С нуля)", callback_data="eng_sc_bar_dating")
        ])
    else:
        kb.append([
            InlineKeyboardButton(text="✍️ Задать свою ситуацию (Магазин, Авто...)", callback_data="eng_create_custom")
        ])
        kb.append([
            InlineKeyboardButton(text="🍸 Знакомство с девушкой в баре (Старт)", callback_data="eng_sc_bar_dating")
        ])

    kb.extend([
        [
            InlineKeyboardButton(text="🎭 Другие ситуации (Отель, Кофе, Такси)", callback_data="eng_menu_scenarios")
        ],
        [
            InlineKeyboardButton(text="📝 Проверочный Квиз (Тест)", callback_data="eng_menu_quizzes"),
            InlineKeyboardButton(text="⚡️ Перевод фразы на лету", callback_data="eng_menu_instant")
        ],
        [
            InlineKeyboardButton(text="📋 Золотые шпаргалки", callback_data="eng_menu_cheats"),
            InlineKeyboardButton(text="📊 Мой уровень & XP", callback_data="eng_menu_profile")
        ],
        [
            InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
        ]
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_scenarios_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора бытовых ситуаций с отображением сохраненного прогресса."""
    all_saved = get_all_saved_dialogs(user_id) if user_id else {}
    kb = [
        [
            InlineKeyboardButton(text="✍️ Задать свою ситуацию (Магазин, Авто...)", callback_data="eng_create_custom")
        ]
    ]
    sc_items = list(SCENARIOS.items())
    for i in range(0, len(sc_items), 2):
        row = []
        for key, data in sc_items[i:i+2]:
            saved = all_saved.get(key)
            if saved and saved.get("turns", 0) > 0:
                t = saved["turns"]
                btn_title = f"{data['title']} (▶️ Р.{t})"
                cb_data = f"eng_resume_{key}"
            else:
                btn_title = f"{data['title']}"
                cb_data = f"eng_sc_{key}"

            row.append(InlineKeyboardButton(
                text=btn_title,
                callback_data=cb_data
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
            InlineKeyboardButton(text="🔄 Начать сначала", callback_data="eng_action_restart")
        ],
        [
            InlineKeyboardButton(text="🎭 Сменить диалог", callback_data="eng_menu_scenarios"),
            InlineKeyboardButton(text="📝 Пройти квиз", callback_data="eng_menu_quizzes")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в меню английского", callback_data="eng_main_menu"),
            InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_back_to_english_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в меню английского и выхода в главное меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад в меню английского", callback_data="eng_main_menu"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


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
            InlineKeyboardButton(text="🔙 Назад в меню английского", callback_data="eng_main_menu"),
            InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
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
            InlineKeyboardButton(text="🔙 Назад в меню английского", callback_data="eng_main_menu"),
            InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
