from aiogram.fsm.state import State, StatesGroup


class SubTrackerStates(StatesGroup):
    waiting_for_sub_text = State()


class CustomRuleStates(StatesGroup):
    waiting_for_rule_text = State()


class ReminderStates(StatesGroup):
    waiting_for_reminder_text = State()


class BirthdayStates(StatesGroup):
    waiting_for_birthday_text = State()


class NoteStates(StatesGroup):
    waiting_for_note_text = State()


class LoanStates(StatesGroup):
    waiting_for_calc_input = State()
