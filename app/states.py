from aiogram.fsm.state import StatesGroup, State

class RegisterState(StatesGroup):
    name = State()
    age = State()
    gender = State()
    about = State()
    city = State()
    photo = State()
    edit_field = State()


class FilterState(StatesGroup):
    age_min = State()
    age_max = State()
    gender = State()
