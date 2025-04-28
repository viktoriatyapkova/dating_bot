from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from random import shuffle

from app.states import RegisterState, FilterState
from app.db.models import UserProfile, UserLike
from app.db.database import get_session
from app.rabbit.producer import publish_profile
from app.rabbit.consumer import get_next_profile
from core.redis import get_redis
from app.tasks import send_like_notification
from fastapi import FastAPI



router = Router()

app = FastAPI()

@app.get("/health")
def read_health():
    return {"status": "ok"}


def main_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="📝 Моя анкета"),
        types.KeyboardButton(text="👀 Смотреть анкеты")
    )
    builder.row(
        types.KeyboardButton(text="📸 Регистрация"),
        types.KeyboardButton(text="✏️ Изменить анкету")
    )
    builder.row(
        types.KeyboardButton(text="🗑 Удалить анкету") 
    )
    return builder.as_markup(resize_keyboard=True)

def format_profile(profile: UserProfile) -> str:
    return (
        f"📝 Анкета:\n\n"
        f"👤 Имя: {profile.name}\n"
        f"🔢 Возраст: {profile.age}\n"
        f"🚻 Пол: {profile.gender}\n"
        f"🏙️ Город: {profile.city}\n"
        f"🎯 Интересы: {profile.interests}\n"
        f"🏷️ Тег: @id{profile.telegram_id}"
    )

def gender_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Мужчина"),
        types.KeyboardButton(text="Женщина")
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def some_function():
    redis_conn = await get_redis()
    await redis_conn.set("mykey", "myvalue")
    value = await redis_conn.get("mykey")
    print(value) 
    

@router.message(F.text.in_(["/start"]))
async def start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в бот знакомств!\nВыбери действие:",
        reply_markup=main_keyboard()
    )

@router.message(F.text == "/reset")
async def reset_state(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔄 Состояние сброшено. Можешь начать заново.")


@router.message(F.text == "/delete_me")
async def delete_me(message: types.Message):
    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == str(message.from_user.id))
        )
        profile = result.scalar_one_or_none()

        if profile:
            await session.delete(profile)
            await session.commit()
            await message.answer("🗑️ Анкета удалена. Можешь зарегистрироваться заново.")
        else:
            await message.answer("❌ Анкета не найдена.")

@router.message(F.text == "📸 Регистрация")
@router.message(F.text.in_(["/register"]))
async def start_registration(message: types.Message, state: FSMContext):
    async with get_session() as session:
        user_exists = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == str(message.from_user.id))
        )
        profile = user_exists.scalars().first()

        if profile:
            await message.answer_photo(
                photo=profile.photo_url,
                caption=f"Ты уже зарегистрирован.\n\n{format_profile(profile)}\n\nХочешь изменить свою анкету?",
                reply_markup=main_keyboard()
            )
            return

    await message.answer("Привет! Как тебя зовут?", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(RegisterState.name)

@router.message(F.text == "📝 Моя анкета")
async def show_profile(message: types.Message):
    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == str(message.from_user.id))
        )
        profile = result.scalars().first()

        if profile:
            await message.answer_photo(
                photo=profile.photo_url,
                caption=format_profile(profile),
                reply_markup=main_keyboard()
            )
        else:
            await message.answer("❌ Ты еще не зарегистрирован!", reply_markup=main_keyboard())

@router.message(RegisterState.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(RegisterState.age)

@router.message(RegisterState.age)
async def reg_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введи корректный возраст (число).")

    await state.update_data(age=int(message.text))
    await message.answer("Укажи свой пол:", reply_markup=gender_keyboard())
    await state.set_state(RegisterState.gender)


@router.message(RegisterState.gender)
async def reg_gender(message: types.Message, state: FSMContext):
    if message.text not in ["Мужчина", "Женщина"]:
        await message.answer("Пожалуйста, выбери пол, используя кнопки ниже:", reply_markup=gender_keyboard())
        return

    await state.update_data(gender=message.text)
    await message.answer("Расскажи немного о себе (интересы, увлечения):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(RegisterState.about)


@router.message(RegisterState.about)
async def reg_about(message: types.Message, state: FSMContext):
    await state.update_data(interests=message.text)
    await message.answer("Из какого ты города?")
    await state.set_state(RegisterState.city)

@router.message(RegisterState.city)
async def reg_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("И последнее — пришли своё фото 📷")
    await state.set_state(RegisterState.photo)


@router.message(F.text.regexp(r'^@id\d+$'))
async def search_profile(message: types.Message):
    telegram_id = message.text.replace('@id', '')
    
    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == telegram_id))
        profile = result.scalars().first()
        
        if profile:
            await message.answer_photo(
                photo=profile.photo_url,
                caption=format_profile(profile),
                reply_markup=main_keyboard()
            )
        else:
            await message.answer("❌ Анкета не найдена!", reply_markup=main_keyboard())

@router.message(F.text == "✏️ Изменить анкету")
async def edit_profile(message: types.Message, state: FSMContext):
    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == str(message.from_user.id))
        )
        profile = result.scalar_one_or_none()

        if not profile:
            await message.answer("❌ Ты ещё не зарегистрирован. Сначала пройди регистрацию.")
            return

        await state.update_data(
            profile_id=profile.id,
            name=profile.name,
            age=profile.age,
            gender=profile.gender,
            interests=profile.interests,
            city=profile.city,
        )

        await message.answer("⚙️ Давай изменим твою анкету. Как тебя зовут?")
        await state.set_state(RegisterState.name)


@router.message(RegisterState.photo, F.photo)
async def save_profile_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id

    async with get_session() as session:
        profile_id = data.get("profile_id")
        
        if profile_id:
            result = await session.execute(select(UserProfile).where(UserProfile.id == profile_id))
            profile = result.scalar_one_or_none()

            if profile:
                profile.name = data["name"]
                profile.age = data["age"]
                profile.gender = data["gender"]
                profile.interests = data["interests"]
                profile.city = data["city"]
                profile.photo_url = photo_id
                await session.commit()

                await message.answer_photo(
                    photo=profile.photo_url,
                    caption=f"✅ Анкета обновлена!\n\n{format_profile(profile)}",
                    reply_markup=main_keyboard()
                )
        else:
            new_profile = UserProfile(
                telegram_id=str(message.from_user.id),
                name=data['name'],
                age=data['age'],
                gender=data['gender'],
                interests=data['interests'],
                city=data['city'],
                photo_url=photo_id
            )
            session.add(new_profile)
            await session.commit()

            await message.answer_photo(
                photo=new_profile.photo_url,
                caption=f"✅ Анкета сохранена!\n\n{format_profile(new_profile)}\n\nТеперь другие пользователи могут найти тебя по тегу @id{new_profile.telegram_id}",
                reply_markup=main_keyboard()
            )

    await state.clear()


@router.message(RegisterState.photo)
async def wrong_photo(message: types.Message):
    await message.answer("Пожалуйста, отправь фото как изображение, не как файл.")

@router.message(F.text == "👀 Смотреть анкеты")
async def ask_age_min(message: types.Message, state: FSMContext):
    await message.answer("🔢 Введи минимальный возраст:")
    await state.set_state(FilterState.age_min)

@router.message(FilterState.age_min)
async def ask_age_max(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи число для минимального возраста.")
        return
    await state.update_data(age_min=int(message.text))
    await message.answer("🔢 Теперь введи максимальный возраст:")
    await state.set_state(FilterState.age_max)

@router.message(FilterState.age_max)
async def ask_gender(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи число для максимального возраста.")
        return
    await state.update_data(age_max=int(message.text))
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Мужчины"),
        types.KeyboardButton(text="Женщины"),
        types.KeyboardButton(text="Все")
    )
    await message.answer("🚻 Кого ищешь?", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(FilterState.gender)

@router.message(FilterState.gender)
async def show_filtered_profiles(message: types.Message, state: FSMContext):
    gender = message.text
    if gender not in ["Мужчины", "Женщины", "Все"]:
        await message.answer("Пожалуйста, выбери из предложенных вариантов.")
        return

    await state.update_data(gender=gender)
    data = await state.get_data()

    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == str(message.from_user.id))
        )
        current_user = result.scalar_one_or_none()

        if not current_user:
            await message.answer("❌ Ты ещё не зарегистрирован.")
            await state.clear()
            return

        query = select(UserProfile).where(
            UserProfile.telegram_id != str(message.from_user.id),
            UserProfile.city == current_user.city,
            UserProfile.age >= data['age_min'],
            UserProfile.age <= data['age_max']
        )

        if data['gender'] == "Мужчины":
            query = query.where(UserProfile.gender == "Мужчина")
        elif data['gender'] == "Женщины":
            query = query.where(UserProfile.gender == "Женщина")

        result = await session.execute(query)
        profiles = result.scalars().all()

        if not profiles:
            await message.answer("😔 Нет анкет, подходящих под твои критерии.", reply_markup=main_keyboard())
            await state.clear()
            return

        shuffle(profiles)


        for profile in profiles:
            await publish_profile({
                "telegram_id": profile.telegram_id,
                "name": profile.name,
                "age": profile.age,
                "gender": profile.gender,
                "city": profile.city,
                "interests": profile.interests,
                "photo_url": profile.photo_url
            })

        await message.answer("Секундочку, подбираю анкеты 🔎", reply_markup=types.ReplyKeyboardRemove())
        await show_profile_by_index(message, state)




def profiles_keyboard(current_index: int, total: int) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="❤️ Лайк",
        callback_data=f"like_{current_index}"
    )

    builder.button(
        text="➡️ Далее",
        callback_data=f"next_{current_index + 1}"
    )

    return builder.as_markup()



async def show_profile_by_index(message: types.Message, state: FSMContext):
    profile_data = await get_next_profile()

    if not profile_data:
        await message.answer("🏁 Вы просмотрели все анкеты!", reply_markup=main_keyboard())
        await state.clear()
        return

    await message.answer_photo(
        photo=profile_data["photo_url"],
        caption=f"📝 Анкета:\n\n"
                f"👤 Имя: {profile_data['name']}\n"
                f"🔢 Возраст: {profile_data['age']}\n"
                f"🚻 Пол: {profile_data['gender']}\n"
                f"🏙️ Город: {profile_data['city']}\n"
                f"🎯 Интересы: {profile_data['interests']}\n"
                f"🏷️ Тег: @id{profile_data['telegram_id']}",
        reply_markup=profiles_keyboard(0, 0) 
    )

    await state.update_data(current_profile=profile_data)


@router.callback_query(F.data.startswith("next_"))
async def next_profile(callback: types.CallbackQuery, state: FSMContext):
    await show_profile_by_index(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("like_"))
async def like_profile(callback: types.CallbackQuery, state: FSMContext):
    from app.bot import bot 

    async with get_session() as session:
        data = await state.get_data()
        current_profile = data.get('current_profile')

        if not current_profile:
            await callback.answer("⚠️ Нет профиля для лайка.")
            return

        user_telegram_id = str(callback.from_user.id)
        user_username = callback.from_user.username

        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == user_telegram_id)
        )
        current_user = result.scalar_one_or_none()

        if not current_user:
            await callback.answer("⚠️ Ваша анкета не найдена. Зарегистрируйтесь сначала.")
            return

        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == current_profile['telegram_id'])
        )
        liked_user = result.scalar_one_or_none()

        if not liked_user:
            await callback.answer("⚠️ Пользователь не найден.")
            return

        existing_like = await session.execute(
            select(UserLike).where(
                UserLike.liker_id == current_user.id,
                UserLike.liked_id == liked_user.id
            )
        )
        if existing_like.scalar():
            await callback.answer("Вы уже ставили лайк этому пользователю.")
            return

        like = UserLike(liker_id=current_user.id, liked_id=liked_user.id)
        session.add(like)
        await session.commit()
        await callback.answer("❤️ Лайк сохранён!")

        reciprocal_like = await session.execute(
            select(UserLike).where(
                UserLike.liker_id == liked_user.id,
                UserLike.liked_id == current_user.id
            )
        )
        if reciprocal_like.scalar():
            match_msg_to_liker = (
                f"🎉 У вас взаимный лайк с [{liked_user.name or 'пользователь'}](tg://user?id={liked_user.telegram_id})!\n"
                "Можете написать пользователю прямо сейчас 😉"
            )
            match_msg_to_liked = (
                f"🎉 У вас взаимный лайк с [{current_user.name or 'пользователь'}](tg://user?id={current_user.telegram_id})!\n"
                "Можете начать общение!"
            )

            try:
                await bot.send_message(
                    liked_user.telegram_id,
                    match_msg_to_liked,
                    parse_mode="Markdown"
                )
                await bot.send_message(
                    current_user.telegram_id,
                    match_msg_to_liker,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка при отправке сообщений о мэтче: {e}")

        else:
            send_like_notification.delay(
                user_id=liked_user.telegram_id,
                liker_name=user_username or str(current_user.telegram_id)
            )

        await show_profile_by_index(callback.message, state)



@router.message(F.text == "🗑 Удалить анкету")
async def delete_profile(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)

    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            await message.answer("❌ У тебя пока нет анкеты для удаления.", reply_markup=main_keyboard())
            return

        await session.execute(
            UserLike.__table__.delete().where(
                (UserLike.liker_id == profile.id) | (UserLike.liked_id == profile.id)
            )
        )

        await session.delete(profile)
        await session.commit()

    await state.clear()
    await message.answer("🗑 Твоя анкета была удалена.", reply_markup=main_keyboard())


