from aiogram.fsm.state import State, StatesGroup


class SupportState(StatesGroup):
    """Состояния для обращения в поддержку"""
    waiting_for_message = State()
    waiting_for_response = State()


class PaymentState(StatesGroup):
    """Состояния для процесса оплаты"""
    choosing_method = State()
    waiting_for_payment = State()
    confirming_payment = State()


class AdminState(StatesGroup):
    """Состояния для административных действий"""
    waiting_for_user_id = State()
    waiting_for_days = State()
    waiting_for_message = State()
    waiting_for_broadcast = State()