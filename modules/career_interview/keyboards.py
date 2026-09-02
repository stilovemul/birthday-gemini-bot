"""
Инлайн-клавиатуры тренажера собеседований для IT QA Manager.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_interview_main_keyboard() -> InlineKeyboardMarkup:
    """Главное стартовое меню выбора направлений собеседования QA Менеджера."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧪 Стратегия & Процессы", callback_data="int_role_strategy"),
                InlineKeyboardButton(text="🤖 Автоматизация (AQA)", callback_data="int_role_automation")
            ],
            [
                InlineKeyboardButton(text="👥 Команда & Найм QA", callback_data="int_role_team"),
                InlineKeyboardButton(text="💥 Факапы & Релизы", callback_data="int_role_incidents")
            ],
            [
                InlineKeyboardButton(text="📊 Метрики & C-Level", callback_data="int_role_metrics"),
                InlineKeyboardButton(text="🎯 Торг об оффере QA", callback_data="int_role_salary")
            ],
            [
                InlineKeyboardButton(text="🇬🇧 Global QA (English)", callback_data="int_role_english"),
                InlineKeyboardButton(text="✍️ Свой QA-кейс", callback_data="int_role_custom")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_interview_action_keyboard(role_key: str = "custom") -> InlineKeyboardMarkup:
    """Клавиатура действий под активным вопросом собеседования QA Менеджера."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💡 Идеальный ответ (STAR)", callback_data=f"int_act_tip_{role_key}"),
                InlineKeyboardButton(text="🔄 Другой вопрос", callback_data=f"int_act_skip_{role_key}")
            ],
            [
                InlineKeyboardButton(text="📊 Итог и Оценка QA-сессии", callback_data=f"int_act_finish_{role_key}"),
                InlineKeyboardButton(text="📋 Сменить тему", callback_data="int_act_roles")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_tip_card_keyboard(role_key: str = "custom") -> InlineKeyboardMarkup:
    """Клавиатура после показа подсказки / идеального ответа STAR."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другой вопрос", callback_data=f"int_act_skip_{role_key}"),
                InlineKeyboardButton(text="📊 Оценить диалог", callback_data=f"int_act_finish_{role_key}")
            ],
            [
                InlineKeyboardButton(text="📋 Другая QA-тема", callback_data="int_act_roles"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_post_scorecard_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после выдачи итогового отчета/оценки QA Scorecard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Новая тренировка QA", callback_data="int_act_roles")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
