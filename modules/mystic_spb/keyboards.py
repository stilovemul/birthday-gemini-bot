"""
Клавиатуры для модуля «Тайный Петербург» и интерактивных пеших экскурсий.
"""

from typing import List, Dict, Any, Optional
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)


def get_spb_gps_mode_keyboard() -> ReplyKeyboardMarkup:
    """Нижняя панель управления в режиме 'Тайный Петербург'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚶‍♂️ Погулять по СПб (Экскурсия)")],
            [KeyboardButton(text="📍 Отправить мою геопозицию", request_location=True)],
            [KeyboardButton(text="🏁 Закончить режим (Главное меню)")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )


def get_mystic_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура знаменитых мистических локаций СПб."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚶‍♂️ Собрать маршрут для прогулки", callback_data="spb_tour_menu")
            ],
            [
                InlineKeyboardButton(text="📍 Гостиница Англетер (Есенин)", callback_data="mspb_loc_angleterre"),
                InlineKeyboardButton(text="🏛 Манежная площадь", callback_data="mspb_loc_manezhnaya")
            ],
            [
                InlineKeyboardButton(text="🏰 Юсуповский дворец (Распутин)", callback_data="mspb_loc_yusupov"),
                InlineKeyboardButton(text="👻 Михайловский замок (Павел I)", callback_data="mspb_loc_castle")
            ],
            [
                InlineKeyboardButton(text="🔫 Черная речка (Пушкин)", callback_data="mspb_loc_pushkin"),
                InlineKeyboardButton(text="🎲 Случайная тайна СПб", callback_data="mspb_loc_random")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_tour_start_keyboard() -> InlineKeyboardMarkup:
    """Выбор популярной начальной точки экскурсии."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏛 Невский / Гостиный Двор", callback_data="spb_tstart_nevsky"),
                InlineKeyboardButton(text="🎭 Сенная / Коломна", callback_data="spb_tstart_sennaya")
            ],
            [
                InlineKeyboardButton(text="🏰 Петроградская сторона", callback_data="spb_tstart_petrogradka"),
                InlineKeyboardButton(text="🌊 Васильевский остров", callback_data="spb_tstart_vasilievsky")
            ],
            [
                InlineKeyboardButton(text="🌲 Чернышевская / Литейная", callback_data="spb_tstart_chernyshevskaya"),
                InlineKeyboardButton(text="📍 Рядом со мной (GPS)", callback_data="spb_tstart_gps")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад к тайнам СПб", callback_data="spb_back_to_mystic"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_tour_selection_keyboard(tours: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Кнопки выбора одного из предложенных маршрутов."""
    buttons = []
    icons = ["🕵️‍♂️", "🍸", "🏛", "☕️", "✨"]

    for idx, tour in enumerate(tours[:3]):
        icon = icons[idx % len(icons)]
        title = tour.get("title", f"Маршрут №{idx+1}")
        # Ограничиваем длину текста на кнопке
        btn_text = f"{icon} Вариант {idx+1}: {title[:32]}"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"spb_tsel_{idx}")
        ])

    buttons.append([
        InlineKeyboardButton(text="🔄 Другая начальная точка", callback_data="spb_tour_menu"),
        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tour_step_keyboard(session: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Кнопки управления текущим шагом пешей экскурсии (по пути к точке)."""
    tour = session.get("tour", {})
    stops = tour.get("stops", [])
    idx = session.get("current_stop_idx", 0)
    stop = stops[idx] if idx < len(stops) else {}

    kb = [
        [
            InlineKeyboardButton(
                text=f"📍 Я на месте (Точка {idx+1}: что тут было?)",
                callback_data=f"spb_tarrived_{idx}"
            )
        ]
    ]

    # Ссылка на Яндекс.Карты
    maps_url = stop.get("maps_url")
    if maps_url:
        kb.append([
            InlineKeyboardButton(text="🗺 Открыть точку на Яндекс.Картах ↗", url=maps_url)
        ])

    # Кнопка культового заведения по пути
    if stop.get("spot_by_the_way"):
        kb.append([
            InlineKeyboardButton(
                text="☕️ Культовое заведение по пути (Меню & фишка)",
                callback_data=f"spb_tvenue_{idx}"
            )
        ])

    kb.append([
        InlineKeyboardButton(text="⏭ Пропустить точку", callback_data=f"spb_tskip_{idx}"),
        InlineKeyboardButton(text="🏁 Завершить экскурсию", callback_data="spb_tcancel")
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_tour_next_navigation_keyboard(session: Dict[str, Any], has_next: bool) -> InlineKeyboardMarkup:
    """Кнопки после рассказа о точке — переход к следующей локации."""
    tour = session.get("tour", {})
    stops = tour.get("stops", [])
    idx = session.get("current_stop_idx", 0)
    next_idx = idx + 1

    kb = []
    if has_next and next_idx < len(stops):
        next_stop = stops[next_idx]
        kb.append([
            InlineKeyboardButton(
                text=f"🚶‍♂️ Идем к Точке {next_idx+1}: {next_stop.get('name', '')[:25]} ➔",
                callback_data=f"spb_tnext_{next_idx}"
            )
        ])
        if next_stop.get("maps_url"):
            kb.append([
                InlineKeyboardButton(
                    text="🗺 Следующая точка на Яндекс.Картах ↗",
                    url=next_stop.get("maps_url")
                )
            ])
        if next_stop.get("spot_by_the_way"):
            kb.append([
                InlineKeyboardButton(
                    text="☕️ Заведение по пути к следующей точке",
                    callback_data=f"spb_tvenue_{next_idx}"
                )
            ])
        kb.append([
            InlineKeyboardButton(text="🏁 Закончить прогулку", callback_data="spb_tcancel")
        ])
    else:
        # Это была последняя точка
        kb.append([
            InlineKeyboardButton(text="🏆 Завершить экскурсию и подвести итоги", callback_data="spb_tfinish")
        ])
        kb.append([
            InlineKeyboardButton(text="🚶‍♂️ Начать новый маршрут", callback_data="spb_tour_menu"),
            InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
        ])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_tour_finish_keyboard() -> InlineKeyboardMarkup:
    """Финишная клавиатура после завершения всей экскурсии."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚶‍♂️ Начать другую пешую экскурсию", callback_data="spb_tour_menu")
            ],
            [
                InlineKeyboardButton(text="🕵️‍♂️ Городские тайны и расследования", callback_data="spb_back_to_mystic"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
