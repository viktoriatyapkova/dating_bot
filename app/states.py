from aiogram.fsm.state import StatesGroup, State

class RegisterState(StatesGroup):
    name = State()
    age = State()
    gender = State()
    about = State()
    city = State()
    photo = State()
