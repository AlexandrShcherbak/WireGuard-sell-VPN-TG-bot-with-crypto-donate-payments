from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Купить подписку", callback_data="buy")
    builder.button(text="📘 Инструкция", callback_data="howto")
    builder.button(text="🎁 Пробный период", callback_data="trial")
    builder.button(text="📞 Поддержка", callback_data="support")
    builder.adjust(1)
    return builder.as_markup()


def get_subscription_keyboard(subscription_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления подпиской"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data=f"pay:{subscription_id}")
    builder.button(text="📋 Инструкция", callback_data="howto")
    builder.button(text="◀️ Назад", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def get_payment_methods_keyboard(subscription_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с выбором способа оплаты"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 CryptoBot", callback_data=f"pay_crypto:{subscription_id}")
    builder.button(text="💝 DonationAlerts", callback_data=f"pay_donation:{subscription_id}")
    builder.button(text="🏦 СБП", callback_data=f"pay_sbp:{subscription_id}")
    builder.button(text="◀️ Назад", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def check_payment_kb(payment_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для проверки оплаты"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить оплату", callback_data=f"check_payment:{payment_id}")
    builder.button(text="◀️ Назад", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def buy_methods_kb(subscription_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора способа оплаты (алиас для get_payment_methods_keyboard)"""
    return get_payment_methods_keyboard(subscription_id)


def main_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура главного меню (алиас для get_main_keyboard)"""
    return get_main_keyboard()
