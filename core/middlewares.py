import logging
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from core.keyboards import MAIN_MENU_BUTTONS, is_exit_command

logger = logging.getLogger("MenuNavigationMiddleware")

# Normalised set of menu buttons (stripping unicode \ufe0f variation selectors and converting to lowercase)
NORMALIZED_MENU_BUTTONS = {
    b.replace("\ufe0f", "").strip().lower() for b in MAIN_MENU_BUTTONS
}

# Common module entry phrases/aliases
MODULE_ENTRY_ALIASES = {
    "загород", "загородный отдых", "загородный семейный отдых", "семейный отдых", "отдых с детьми",
    "рестораны", "гастро-локатор", "кафе", "спикизи-бары", "бары",
    "выходные", "выходные & дети", "роадтрип", "афиша",
    "кино", "погода", "сон", "кредиты", "сейф", "кбжу", "еда", "шеф-ужин"
}


def is_menu_navigation(text: str) -> bool:
    """
    Checks whether the given message text represents a main menu button,
    a module shortcut, or a slash command (excluding exit commands).
    """
    if not text:
        return False
    cleaned = text.replace("\ufe0f", "").strip().lower()
    if cleaned in NORMALIZED_MENU_BUTTONS or cleaned in MODULE_ENTRY_ALIASES:
        return True
    # Slash commands that are NOT exit commands
    if text.startswith("/") and not is_exit_command(text):
        return True
    return False


class MenuNavigationMiddleware(BaseMiddleware):
    """
    Outer middleware for message updates.
    Whenever a user in any active FSM state sends a main menu button,
    module alias, or slash command, this middleware automatically resets
    the old state and clears raw_state from the dispatch context.
    This guarantees that the target module's entry handler receives the update
    instead of the previous state handler intercepting it as a text query.
    """
    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.text:
            if is_menu_navigation(event.text):
                state: FSMContext = data.get("state")
                if state:
                    current_state = await state.get_state()
                    if current_state is not None:
                        logger.info(
                            f"Menu navigation detected ('{event.text}'). "
                            f"Resetting active state '{current_state}' for user {event.from_user.id}."
                        )
                        await state.clear()
                        data["raw_state"] = None
        return await handler(event, data)
