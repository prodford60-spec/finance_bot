from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from yookassa import Configuration, Payment
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, SUBSCRIPTION_PRICE
from database import activate_subscription
import uuid

router = Router()

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

def create_payment_link(user_id: int, amount: int):
    idempotence_key = str(uuid.uuid4())
    payment = Payment.create({
        "amount": {
            "value": f"{amount}.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            # Замени на username своего бота
            "return_url": "https://t.me/my_finance_helper_bot"
        },
        "capture": True,
        "description": f"Подписка. User ID: {user_id}",
        "metadata": {
            "user_id": str(user_id)
        }
    }, idempotence_key)

    return payment.confirmation.confirmation_url, payment.id

@router.callback_query(F.data == "subscribe")
async def subscribe_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    try:
        pay_url, payment_id = create_payment_link(user_id, SUBSCRIPTION_PRICE)

        text = (
            "💳 *Оформление подписки*\n\n"
            f"Стоимость: *{SUBSCRIPTION_PRICE} ₽/месяц*\n\n"
            "1. Нажмите кнопку «Оплатить»\n"
            "2. Завершите оплату на сайте\n"
            "3. Вернитесь и нажмите «Проверить оплату»\n\n"
            "🔒 Оплата через ЮKassa — безопасно"
        )

        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить 199 ₽", url=pay_url)],
                [InlineKeyboardButton(
                    text="✅ Проверить оплату",
                    callback_data=f"check_payment:{payment_id}"
                )],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_start")]
            ])
        )
    except Exception as e:
        await callback.message.edit_text(
            "❌ Ошибка при создании платежа. Проверьте ключи ЮKassa в .env файле.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_start")]
            ])
        )

@router.callback_query(F.data.startswith("check_payment:"))
async def check_payment(callback: CallbackQuery):
    payment_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    try:
        payment = Payment.find_one(payment_id)

        if payment.status == "succeeded":
            new_end = await activate_subscription(user_id, days=30)
            await callback.message.edit_text(
                f"🎉 *Оплата прошла успешно!*\n\n"
                f"✅ Подписка активна до {new_end.strftime('%d.%m.%Y')}\n\n"
                "Теперь задавайте вопросы финансовому советнику!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="💬 Задать вопрос", callback_data="ask_ai"
                    )]
                ])
            )
        elif payment.status == "pending":
            await callback.answer(
                "⏳ Оплата ещё не завершена. Завершите и попробуйте снова.",
                show_alert=True
            )
        else:
            await callback.answer(
                "❌ Оплата не прошла. Попробуйте ещё раз.",
                show_alert=True
            )
    except Exception:
        await callback.answer(
            "❌ Не удалось проверить оплату. Попробуйте позже.",
            show_alert=True
        )