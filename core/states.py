from aiogram.fsm.state import State, StatesGroup


class ActiveModeStates(StatesGroup):
    # Gourmet
    breakfast_mode = State()
    barman_mode = State()
    
    # Freebies & Promos
    promos_mode = State()
    games_mode = State()
    
    # Auto Legal
    dtp_mode = State()
    rights_mode = State()
    fine_dispute_mode = State()
    
    # Research & Fact-Check
    research_mode = State()
    factcheck_mode = State()
    
    # Anti-Spam
    antispam_mode = State()
    
    # AI General Chat
    gemini_chat_mode = State()


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
