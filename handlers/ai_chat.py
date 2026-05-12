from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from database import is_subscribed

router = Router()
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Ты — опытный финансовый советник и коуч.
Ты отвечаешь на вопросы о личных финансах, опираясь на идеи из популярных книг:

1. «Богатый папа, бедный папа» Роберта Кийосаки — активы vs пассивы, финансовая свобода
2. «Думай и богатей» Наполеона Хилла — мышление богатого человека, цели
3. «Самый богатый человек в Вавилоне» Джорджа Клейсона — правило 10%, бюджет
4. «Психология денег» Моргана Хаузела — поведение с деньгами, долгосрочное мышление
5. «Разумный инвестор» Бенджамина Грэма — инвестиции, диверсификация
6. «Ваши деньги или ваша жизнь» Вики Робин — осознанные траты
7. «Автоматический миллионер» Дэвида Бака — автоматизация финансов

Правила:
- Отвечай на русском языке
- Давай конкретные практичные советы
- Ссылайся на книги когда уместно
- Используй простой язык без сложных терминов
- Отвечай кратко — максимум 3-5 абзацев"""

BOOK_TIPS = [
    ("💰 Правило 10% (Клейсон)",
     "«Самый богатый человек в Вавилоне» учит: *откладывай минимум 10% от каждого дохода*.\n\n"
     "Получил 50 000 ₽ — сразу отложи 5 000 ₽. Не думай об этом, просто делай автоматически.\n\n"
     "Эти деньги — твоя армия, которая работает на тебя пока ты спишь."),
    ("📊 Активы vs Пассивы (Кийосаки)",
     "Кийосаки объясняет просто:\n\n"
     "✅ *Актив* — кладёт деньги в твой карман (акции, аренда, бизнес)\n"
     "❌ *Пассив* — вытаскивает деньги из кармана (кредиты, дорогая машина)\n\n"
     "Богатые покупают активы. Бедные покупают пассивы, думая что это активы."),
    ("🧠 Психология трат (Хаузел)",
     "Морган Хаузел говорит: *самое важное в финансах — поведение, а не знания*.\n\n"
     "Можно знать всё об инвестициях, но паниковать и продавать акции на падении.\n\n"
     "Решение: автоматизируй финансы так, чтобы эмоции не мешали."),
    ("🎯 Сила сложного процента (Грэм)",
     "Бенджамин Грэм учил: *время — главный актив инвестора*.\n\n"
     "10 000 ₽ под 10% годовых:\n"
     "• Через 10 лет → 25 937 ₽\n"
     "• Через 20 лет → 67 275 ₽\n"
     "• Через 30 лет → 174 494 ₽\n\n"
     "Начни сегодня, даже с маленькой суммы."),
    ("🚀 Заплати сначала себе (Бак)",
     "Дэвид Бак советует: *настрой автоплатёж на накопительный счёт в день зарплаты*.\n\n"
     "1. Получил зарплату\n"
     "2. Автоматически 10-20% ушло на накопления\n"
     "3. Живёшь на остаток\n\n"
     "Так ты никогда не «забудешь» откладывать."),
]

class AskAI(StatesGroup):
    waiting_for_question = State()

@router.callback_query(F.data == "ask_ai")
async def ask_ai_start(callback: CallbackQuery, state: FSMContext):
    if not await is_subscribed(callback.from_user.id):
        await callback.answer("❌ Нужна активная подписка!", show_alert=True)
        return

    await state.set_state(AskAI.waiting_for_question)
    await callback.message.edit_text(
        "💬 *Задайте ваш финансовый вопрос:*\n\n"
        "Например:\n"
        "• Как начать откладывать деньги?\n"
        "• Куда вложить 50 000 рублей?\n"
        "• Как выбраться из долгов?\n"
        "• Что такое пассивный доход?\n\n"
        "Напишите ваш вопрос 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_ai")]
        ])
    )

@router.message(AskAI.waiting_for_question)
async def process_ai_question(message: Message, state: FSMContext):
    if not await is_subscribed(message.from_user.id):
        await state.clear()
        await message.answer("❌ Подписка истекла. Оформите новую.")
        return

    await state.clear()
    thinking_msg = await message.answer("🤔 Анализирую ваш вопрос...")

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            max_tokens=800,
            temperature=0.7
        )

        answer = response.choices[0].message.content

        await thinking_msg.edit_text(
            f"💡 *Ответ финансового советника:*\n\n{answer}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Ещё вопрос", callback_data="ask_ai")],
                [InlineKeyboardButton(text="📚 Советы из книг", callback_data="book_tips")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_start")]
            ])
        )
    except Exception:
        await thinking_msg.edit_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_start")]
            ])
        )

@router.callback_query(F.data == "cancel_ai")
async def cancel_ai(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.start import main_menu
    is_sub = await is_subscribed(callback.from_user.id)
    await callback.message.edit_text(
        "Главное меню 👇",
        reply_markup=main_menu(is_sub)
    )

@router.callback_query(F.data == "book_tips")
async def book_tips_handler(callback: CallbackQuery):
    if not await is_subscribed(callback.from_user.id):
        await callback.answer("❌ Нужна активная подписка!", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text=tip[0], callback_data=f"tip:{i}")]
        for i, tip in enumerate(BOOK_TIPS)
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_start")])

    await callback.message.edit_text(
        "📚 *Советы из книг по финансовой грамотности:*\n\nВыберите тему:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(F.data.startswith("tip:"))
async def show_tip(callback: CallbackQuery):
    tip_index = int(callback.data.split(":")[1])
    title, content = BOOK_TIPS[tip_index]

    await callback.message.edit_text(
        f"{title}\n\n{content}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К советам", callback_data="book_tips")],
            [InlineKeyboardButton(text="💬 Задать вопрос ИИ", callback_data="ask_ai")]
        ])
    )