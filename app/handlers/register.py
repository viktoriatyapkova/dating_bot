from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from random import shuffle
import re

from app.states import RegisterState
from app.db.models import UserProfile, UserLike
from app.db.database import get_session

router = Router()

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
    await message.answer("Укажи свой пол (М/Ж/Другое):")
    await state.set_state(RegisterState.gender)

@router.message(RegisterState.gender)
async def reg_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Расскажи немного о себе (интересы, увлечения):")
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
async def show_random_profiles(message: types.Message, state: FSMContext):
    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(
                UserProfile.telegram_id != str(message.from_user.id)
        ))
        profiles = result.scalars().all()

        if not profiles:
            await message.answer("😔 Пока нет других анкет для просмотра")
            return

        shuffle(profiles)
        await state.update_data(
            profiles=[p.telegram_id for p in profiles],
            current_index=0
        )

        await show_profile_by_index(message, state)

def profiles_keyboard(current_index: int, total: int) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="❤️ Лайк",
        callback_data=f"like_{current_index}"
    )

    if current_index + 1 < total:
        builder.button(
            text="➡️ Далее",
            callback_data=f"next_{current_index + 1}"
        )

    return builder.as_markup()


async def show_profile_by_index(message: types.Message, state: FSMContext):
    data = await state.get_data()
    profiles = data.get('profiles', [])
    current_index = data.get('current_index', 0)
    
    if current_index >= len(profiles):
        await message.answer("🏁 Вы просмотрели все анкеты!")
        await state.clear()
        return

    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(
                UserProfile.telegram_id == profiles[current_index]
            )
        )
        profile = result.scalars().first()

    if profile:
        await message.answer_photo(
            photo=profile.photo_url,
            caption=f"{format_profile(profile)}\n\n"
                    f"Анкета {current_index + 1} из {len(profiles)}",
            reply_markup=profiles_keyboard(current_index, len(profiles))
        )
    else:
        await state.update_data(current_index=current_index + 1)
        await show_profile_by_index(message, state)

@router.callback_query(F.data.startswith("next_"))
async def next_profile(callback: types.CallbackQuery, state: FSMContext):
    new_index = int(callback.data.split("_")[1])
    await state.update_data(current_index=new_index)
    await show_profile_by_index(callback.message, state)
    await callback.answer()



@router.callback_query(F.data.startswith("like_"))
async def like_profile(callback: types.CallbackQuery, state: FSMContext):
    profile_index = int(callback.data.split("_")[1])
    user_telegram_id = str(callback.from_user.id)

    async with get_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == user_telegram_id)
        )
        current_user = result.scalar_one_or_none()

        if not current_user:
            await callback.answer("⚠️ Ваша анкета не найдена. Зарегистрируйтесь сначала.")
            return

        data = await state.get_data()
        profiles = data.get("profiles", [])
        if profile_index >= len(profiles):
            await callback.answer("⚠️ Анкета не найдена.")
            return

        liked_telegram_id = profiles[profile_index]

        result = await session.execute(
            select(UserProfile).where(UserProfile.telegram_id == liked_telegram_id)
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

        new_index = profile_index + 1
        if new_index >= len(profiles):
            await callback.message.answer("🏁 Вы просмотрели все анкеты!")
            await state.clear()
        else:
            await state.update_data(current_index=new_index)
            await show_profile_by_index(callback.message, state)

        reverse_like = await session.execute(
            select(UserLike).where(
                UserLike.liker_id == liked_user.id,
                UserLike.liked_id == current_user.id
            )
        )
        if reverse_like.scalar():
            print(f'liked_user.telegram_id {liked_user.telegram_id}')
            match_msg_to_liker = (
                f"🎉 У вас взаимный лайк с [{liked_user.name}](tg://user?id={liked_user.telegram_id})!\n"
                "Можете написать пользователю прямо сейчас 😉"
            )
            print(f'liked_user.telegram_id {current_user.telegram_id}')
            match_msg_to_liked = (
                f"🎉 У вас взаимный лайк с [{current_user.name}](tg://user?id={current_user.telegram_id})!\n"
                "Можете начать общение!"
            )

            try:
                await callback.bot.send_message(
                    liked_user.telegram_id,
                    match_msg_to_liked,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка при отправке мэтча liked_user: {e}")

            try:
                await callback.message.answer(
                    match_msg_to_liker,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка при отправке мэтча current_user: {e}")



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



