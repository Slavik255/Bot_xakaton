import logging
import re

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types

import api
import io
from config import TG_API_TOKEN
from state import State
from data import RequestData


logging.basicConfig(level=logging.INFO)

bot = Bot(token=TG_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message):
    services = [
        ('Составить заявку', 'new_request'),
    ]
    RequestData.services = services
    buttons = [types.InlineKeyboardButton(service[0], callback_data=service[1]) for service in services]
    
    choose_keyboard = types.InlineKeyboardMarkup()
    choose_keyboard.add(*buttons)
    
    await State.EMPTY.set()
    await message.answer(f'Здравствуйте, {message.from_user.first_name}.', reply_markup=choose_keyboard)


# Новый запрос
@dp.callback_query_handler(text='new_request', state=State.EMPTY)
async def new_request(query: types.CallbackQuery):
    categories_keyboard = types.InlineKeyboardMarkup()

    try:
        categories_json = api.get_categories()
    except:
        return

    categories = []
    for category in categories_json['data']:
        categories.append([category['id'], category['title']])
        categories_keyboard.add(types.InlineKeyboardButton(category['title'], callback_data=category['title']))
    RequestData.categories = categories

    await query.message.answer('Выберите категорию заявки:', reply_markup=categories_keyboard)
    await State.CATEGORY_SELECTION.set()
    await query.answer()


# Выбор категории
@dp.callback_query_handler(state=State.CATEGORY_SELECTION)
async def select_category(query: types.CallbackQuery):
    for category in RequestData.categories:
        if category[1] == query.data:
            id = category[0]
    
    RequestData.data[query.from_user.id] = {}
    RequestData.data[query.from_user.id]['problemCategories'] = [id]
    
    await query.message.answer('Введите ФИО')
    await State.FULL_NAME_INPUT.set()
    await query.answer()


# Ввод ФИО
@dp.message_handler(state=State.FULL_NAME_INPUT)
async def full_name_input(message: types.Message):
    full_name = message.text

    try:
        if len(full_name.split()) != 3:
            raise
        if not full_name.replace(' ', '').isalpha():
            raise
    except:
        await message.answer('Введите корректное ФИО')
        return
    
    RequestData.data[message.from_user.id]['fio'] = message.text

    await State.PHONE_NUMBER_INPUT.set()
    await message.answer('Введите номер телефона (071XXXXXXX)')


# Ввод номера телефона
@dp.message_handler(state=State.PHONE_NUMBER_INPUT)
async def phone_number_inputs(message: types.Message):
    phone_number = message.text

    if re.match(r'^071\d{7}$', phone_number) is None:
        await message.answer('Введите корректный номер телефона')
        return
    
    RequestData.data[message.from_user.id]['phone'] = message.text
    RequestData.data[message.from_user.id]['content'] = [] 
    RequestData.upload = True

    await State.LOCATION_INPUT.set()
    await message.answer('Отправьте фотографии')


# Выбор фотографии
@dp.message_handler(content_types=types.ContentType.PHOTO, state='*')
async def image_selection(message: types.Message):
    if RequestData.upload:
        RequestData.upload = False
        await message.answer('Отправьте геолокацию')

    photo = await bot.download_file_by_id(message.photo[-1].file_id)
    photo_bytes = io.BytesIO()
    photo_bytes.write(photo.getvalue())
    photo_url = api.get_photo_url(photo_bytes.getvalue())
    RequestData.data[message.from_user.id]['content'].append({'type': 0, 'url': photo_url})


# Отправка геолокации
@dp.message_handler(state=State.LOCATION_INPUT)
async def address_input(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Отправить', request_location=True))
    await message.answer('Отправьте геолокацию', reply_markup=keyboard)


# Обработка данных геолокации
@dp.message_handler(content_types=types.ContentType.LOCATION, state=State.LOCATION_INPUT)
async def location(message: types.Message):
    RequestData.data[message.from_user.id]['latitude'] = message.location.latitude
    RequestData.data[message.from_user.id]['longitude'] = message.location.longitude
    await State.DESCRIPTION_INPUT.set()
    await message.answer('Введите описание', reply_markup=types.ReplyKeyboardRemove())


# Ввод описания
@dp.message_handler(state=State.DESCRIPTION_INPUT)
async def description_input(message: types.Message):
    RequestData.data[message.from_user.id]['description'] = message.text

    await State.EMAIL_INPUT.set()
    await message.answer('Введите e-mail')


# Ввод электронной почты
@dp.message_handler(state=State.EMAIL_INPUT)
async def description_input_handler(message: types.Message):
    RequestData.data[message.from_user.id]['email'] = message.text

    try:
        api.send_request(message.from_user.id)
        await message.answer('Заявка отправлена')
    except:
        return
    

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)