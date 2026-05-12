from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from database import create_user, get_user, is_subscribed
from datetime import datetime

router = Router()

def main_menu(is_sub: bool) -> InlineKeyboardMarkup:
    buttons = []
    if is_sub:
        buttons.append([InlineKeyboardButton(
            text="💬 Задать вопрос ИИ-советнику", callback_data="ask_ai"
        )])
        buttons.append([InlineKeyboardButton(
            text="📚 Советы из книг", callback_data="book_tips"
        )])
        buttons.append([InlineKeyboardButton(
            text="📊 Мой статус подписки", callback_data="my_status"
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text="🔓 Оформить подписку — 199 ₽/мес", callback_data="subscribe"
        )])
        buttons.append([InlineKeyboardButton(
            text="ℹ️ Что умеет бот?", callback_data="about"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    await create_user(user_id, username)
    is_sub = await is_subscribed(user_id)

    if is_sub:
        text = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "✅ Ваша подписка активна.\n\n"
            "Я — ваш личный финансовый помощник на основе ИИ.\n"
            "Задавайте вопросы о финансах, инвестициях и экономии."
        )
    else:
        text = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Я — финансовый помощник с ИИ 🤖\n\n"
            "📚 Даю советы на основе книг:\n"
            "• «Богатый папа, бедный папа» — Кийосаки\n"
            "• «Думай и богатей» — Наполеон Хилл\n"
            "• «Самый богатый человек в Вавилоне» — Клейсон\n"
            "• «Психология денег» — Морган Хаузел\n"
            "• «Разумный инвестор» — Бенджамин Грэм\n\n"
            "💳 Подписка: всего 199 ₽/месяц"
        )

    await message.answer(text, reply_markup=main_menu(is_sub))

@router.callback_query(F.data == "about")
async def about_bot(callback: CallbackQuery):
    text = (
        "🤖 *Что умеет этот бот:*\n\n"
        "• Отвечает на вопросы о личных финансах\n"
        "• Даёт советы по экономии и инвестициям\n"
        "• Объясняет финансовые понятия простым языком\n"
        "• Помогает составить план выхода из долгов\n"
        "• Рассказывает о стратегиях из популярных книг\n\n"
        "💡 Всё это за 199 ₽/месяц!"
    )
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оформить подписку", callback_data="subscribe")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_start")]
        ])
    )

@router.callback_query(F.data == "my_status")
async def my_status(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if user and user[2]:
        sub_until = datetime.fromisoformat(user[2])
        days_left = (sub_until - datetime.now()).days
        text = (
            f"📊 *Ваша подписка:*\n\n"
            f"✅ Активна до: {sub_until.strftime('%d.%m.%Y')}\n"
            f"⏳ Осталось дней: {days_left}"
        )
    else:
        text = "❌ У вас нет активной подписки."

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_start")]
        ])
    )

@router.callback_query(F.data == "back_start")
async def back_to_start(callback: CallbackQuery):
    is_sub = await is_subscribed(callback.from_user.id)
    await callback.message.edit_text(
        "Главное меню 👇",
        reply_markup=main_menu(is_sub)
    )