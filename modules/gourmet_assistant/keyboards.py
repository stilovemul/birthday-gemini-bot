from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
from modules.gourmet_assistant.curated_catalog import CURATED_PRESETS


def get_gourmet_main_keyboard() -> InlineKeyboardMarkup:
    """Главная витрина модуля «Еда» со всеми 12 категориями."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍳 Завтрак за 10 мин", callback_data="gourmet_cat_breakfast"),
                InlineKeyboardButton(text="⚡️ Блюда за 15 мин", callback_data="gourmet_cat_express")
            ],
            [
                InlineKeyboardButton(text="🌯 ПП-Фастфуд", callback_data="gourmet_cat_fastfood"),
                InlineKeyboardButton(text="🧊 Шеф из холодильника", callback_data="gourmet_cat_fridge")
            ],
            [
                InlineKeyboardButton(text="🥩 Таймер стейков", callback_data="gourmet_cat_steak"),
                InlineKeyboardButton(text="🍢 Маринад шашлыка", callback_data="gourmet_cat_shashlik")
            ],
            [
                InlineKeyboardButton(text="📅 Меню на неделю + Список", callback_data="gourmet_cat_mealplan"),
                InlineKeyboardButton(text="🥫 Соусы шефов", callback_data="gourmet_cat_sauces")
            ],
            [
                InlineKeyboardButton(text="🍜 Азиатская кухня", callback_data="gourmet_cat_asian"),
                InlineKeyboardButton(text="🍺 Пивной сомелье", callback_data="gourmet_cat_beer")
            ],
            [
                InlineKeyboardButton(text="🍷 Вино, Водка, Коньяк & Алкоголь", callback_data="gourmet_cat_wine_spirits")
            ],
            [
                InlineKeyboardButton(text="🍸 AI-Бармен & Коктейли", callback_data="gourmet_cat_barman")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_category_presets_keyboard(category: str) -> InlineKeyboardMarkup:
    """Клавиатура быстрых шеф-пресетов для выбранной категории."""
    presets = CURATED_PRESETS.get(category, [])
    buttons = []
    
    # For beer and wine/spirits, highlight the shelf photo scanning feature
    if category == "beer":
        buttons.append([InlineKeyboardButton(text="📸 Сфоткать полку с пивом (ИИ выберет лучшее)", callback_data="gourmet_tip_shelf_beer")])
    elif category == "wine_spirits":
        buttons.append([InlineKeyboardButton(text="📸 Сфоткать винную полку / витрину (ИИ выберет)", callback_data="gourmet_tip_shelf_wine_spirits")])

    # Add preset buttons in pairs or single
    for p in presets:
        buttons.append([InlineKeyboardButton(text=p["title"], callback_data=f"gourmet_pr_{p['id']}")])
    
    nav_row = [
        InlineKeyboardButton(text="🎲 Случайный рецепт", callback_data=f"gourmet_rnd_{category}"),
        InlineKeyboardButton(text="🍽 Все категории", callback_data="gourmet_back_to_menu")
    ]
    exit_row = [
        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
    ]
    buttons.append(nav_row)
    buttons.append(exit_row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_gourmet_result_keyboard(category: str, has_shoplist: bool = True) -> InlineKeyboardMarkup:
    """
    Клавиатура под готовым рецептом / напитком:
    - [ 🔄 Другой рецепт (Ещё) ] на первом месте
    - [ 🛒 Список покупок в магазин ]
    - Быстрые кнопки других пресетов этой категории
    - Возврат в кулинарный центр и Главное меню
    """
    rows = [
        [
            InlineKeyboardButton(text="🔄 Другой рецепт (Ещё)", callback_data=f"gourmet_more_{category}")
        ]
    ]

    if has_shoplist:
        rows.append([
            InlineKeyboardButton(text="🛒 Список покупок в магазин", callback_data=f"gourmet_shoplist_{category}")
        ])

    # Contextual quick presets
    presets = CURATED_PRESETS.get(category, [])
    if len(presets) >= 2:
        rows.append([
            InlineKeyboardButton(text=presets[0]["title"], callback_data=f"gourmet_pr_{presets[0]['id']}"),
            InlineKeyboardButton(text=presets[1]["title"], callback_data=f"gourmet_pr_{presets[1]['id']}")
        ])
    elif len(presets) == 1:
        rows.append([
            InlineKeyboardButton(text=presets[0]["title"], callback_data=f"gourmet_pr_{presets[0]['id']}")
        ])

    rows.append([
        InlineKeyboardButton(text="🍽 Меню кулинарии", callback_data="gourmet_back_to_menu"),
        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
