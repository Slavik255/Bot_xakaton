from aiogram.dispatcher.filters.state import State, StatesGroup


class State(StatesGroup):
    EMPTY = State()
    CATEGORY_SELECTION = State()
    FULL_NAME_INPUT = State()
    PHONE_NUMBER_INPUT = State()
    IMAGE_SELECTION = State()
    LOCATION_INPUT = State()
    DESCRIPTION_INPUT = State()
    EMAIL_INPUT = State()