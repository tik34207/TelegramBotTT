import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from config import API_TOKEN, ADMIN_ID
import database as db
import get_code as gc

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

db.init_db()

# Specify the allowed user ID
ALLOWED_USER_ID = 7499521075

class Form(StatesGroup):
    action = State()
    country = State()
    new_country = State()
    number_of_accounts = State()
    file_upload = State()
    delete_country = State()
    custom_number = State()
    admin_panel = State()
    confirm_delete_all = State()
    account_format = State()
    manage_formats = State()
    new_format = State()
    delete_format = State()
    get_code = State()

def get_countries_keyboard(include_new_country=True):
    countries = db.get_countries()
    buttons = [types.InlineKeyboardButton(country[1], callback_data=f"country_{country[1]}") for country in countries]
    if include_new_country:
        buttons.append(types.InlineKeyboardButton('Новая страна', callback_data='new_country'))
    buttons.append(types.InlineKeyboardButton('Назад', callback_data='back_to_main'))
    return types.InlineKeyboardMarkup().add(*buttons)

def get_main_keyboard():
    buttons = [
        types.InlineKeyboardButton(text='Добавить аккаунты', callback_data='add_accounts'),
        types.InlineKeyboardButton(text='Получить аккаунты', callback_data='get_accounts'),
        types.InlineKeyboardButton(text='Просмотреть аккаунты', callback_data='view_accounts'),
        types.InlineKeyboardButton(text='Удалить страну', callback_data='delete_country'),
        types.InlineKeyboardButton(text='Панель администратора', callback_data='admin_panel'),
        types.InlineKeyboardButton(text='Получить код', callback_data='get_code')
    ]
    return types.InlineKeyboardMarkup().add(*buttons)

def get_back_keyboard():
    buttons = [types.InlineKeyboardButton("Назад", callback_data="back_to_main")]
    return types.InlineKeyboardMarkup().add(*buttons)

def get_retry_keyboard():
    buttons = [types.InlineKeyboardButton("Повторить", callback_data="retry_get_code")]
    buttons.append(types.InlineKeyboardButton("Назад", callback_data="back_to_main"))
    return types.InlineKeyboardMarkup().add(*buttons)

def get_admin_keyboard():
    buttons = [
        types.InlineKeyboardButton(text='Общее кол-во аккаунтов', callback_data='total_accounts'),
        types.InlineKeyboardButton(text='Удалить все аккаунты', callback_data='delete_all_accounts'),
        types.InlineKeyboardButton(text='Статистика', callback_data='stats'),
        types.InlineKeyboardButton(text='Отлега', callback_data='account_info'),
        types.InlineKeyboardButton(text='Форматы', callback_data='manage_formats'),
        types.InlineKeyboardButton("В меню", callback_data="back_to_main")
    ]
    return types.InlineKeyboardMarkup().add(*buttons)

def get_number_keyboard():
    buttons = [types.InlineKeyboardButton(str(i), callback_data=f"number_{i}") for i in range(1, 11)]
    buttons.append(types.InlineKeyboardButton("Ввести свое значение", callback_data="custom_number"))
    buttons.append(types.InlineKeyboardButton("Назад", callback_data="back_to_admin"))
    return types.InlineKeyboardMarkup().add(*buttons)

def get_formats_keyboard(include_delete_format=True):
    formats = db.get_formats()
    buttons = [types.InlineKeyboardButton(format, callback_data=f"format_{format}") for format in formats]
    buttons.append(types.InlineKeyboardButton('Добавить формат', callback_data='add_format'))
    if include_delete_format:
        buttons.append(types.InlineKeyboardButton('Удалить формат', callback_data='delete_format'))
    buttons.append(types.InlineKeyboardButton("Назад", callback_data="back_to_admin"))
    return types.InlineKeyboardMarkup().add(*buttons)

def is_allowed_user(user_id):
    return user_id == ALLOWED_USER_ID

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if not is_allowed_user(message.from_user.id):
        await message.reply("У вас нет доступа к этому боту.")
        return
    await Form.action.set()
    await message.reply("Привет! Я бот для управления аккаунтами. Выберите действие:", reply_markup=get_main_keyboard())

@dp.callback_query_handler(lambda c: c.data in ['add_accounts', 'get_accounts', 'view_accounts', 'delete_country', 'admin_panel', 'get_code'], state=Form.action)
async def process_action(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    action = callback_query.data
    await state.update_data(action=action)
    if action == 'add_accounts':
        await Form.country.set()
        await bot.edit_message_text("Выберите страну или добавьте новую:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_countries_keyboard())
    elif action == 'get_accounts':
        await Form.country.set()
        await bot.edit_message_text("Выберите страну:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_countries_keyboard())
    elif action == 'view_accounts':
        accounts = db.view_accounts()
        country_accounts = {}
        for country, account in accounts:
            if country in country_accounts:
                country_accounts[country] += 1
            else:
                country_accounts[country] = 1
        response = '\n'.join([f"{country}: {count} аккаунтов" for country, count in country_accounts.items()])
        await bot.edit_message_text(response or "Нет доступных аккаунтов.", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_back_keyboard())
    elif action == 'delete_country':
        await Form.delete_country.set()
        await bot.edit_message_text("Выберите страну для удаления:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_countries_keyboard())
    elif action == 'admin_panel':
        await Form.admin_panel.set()
        await bot.edit_message_text("Панель администратора:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_admin_keyboard())
    elif action == 'get_code':
        await Form.get_code.set()
        await bot.edit_message_text("Отправьте аккаунт в формате mail|mailpass|login|pass|refreshtoken|clientid.", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_back_keyboard())

@dp.message_handler(state=Form.get_code)
async def handle_get_code(message: types.Message, state: FSMContext):
    if not is_allowed_user(message.from_user.id):
        await message.reply("У вас нет доступа к этому боту.")
        return
    email_address, refreshtoken, clientid = gc.extract_tokens(message.text)
    if email_address and refreshtoken and clientid:
        await state.update_data(email_address=email_address, refreshtoken=refreshtoken, clientid=clientid)
        access_token = gc.get_access_token(refreshtoken, clientid)
        if access_token:
            code = gc.get_code_from_email_hotmail(email_address, access_token)
            if code:
                await message.reply(f"Ваш код TikTok: {code}")
            else:
                await message.reply("Код не найден. Попробуйте еще раз.", reply_markup=get_retry_keyboard())
        else:
            await message.reply("Ошибка при получении токена доступа.", reply_markup=get_retry_keyboard())
    else:
        await message.reply("Некорректный формат. Пожалуйста, отправьте аккаунт в формате mail|mailpass|login|pass|refreshtoken|clientid.", reply_markup=get_retry_keyboard())
    await state.finish()  # Завершаем состояние после отправки всех сообщений
    await message.reply("Привет! Я бот для управления аккаунтами. Выберите действие:", reply_markup=get_main_keyboard())  # Отправка меню

@dp.callback_query_handler(lambda c: c.data == 'retry_get_code', state='*')
async def retry_get_code(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    user_data = await state.get_data()
    email_address = user_data.get('email_address')
    refreshtoken = user_data.get('refreshtoken')
    clientid = user_data.get('clientid')
    if email_address and refreshtoken and clientid:
        access_token = gc.get_access_token(refreshtoken, clientid)
        if access_token:
            code = gc.get_code_from_email_hotmail(email_address, access_token)
            if code:
                await bot.send_message(callback_query.from_user.id, f"Ваш код TikTok: {code}")
                await bot.send_message(callback_query.from_user.id, "Привет! Я бот для управления аккаунтами. Выберите действие:", reply_markup=get_main_keyboard())
            else:
                await bot.send_message(callback_query.from_user.id, "Код не найден. Попробуйте еще раз.", reply_markup=get_retry_keyboard())
        else:
            await bot.send_message(callback_query.from_user.id, "Ошибка при получении токена доступа.", reply_markup=get_retry_keyboard())
    else:
        await bot.send_message(callback_query.from_user.id, "Сессия истекла. Пожалуйста, отправьте аккаунт заново.", reply_markup=get_main_keyboard())
        await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('country_'), state=[Form.country, Form.delete_country])
async def handle_country(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    country = callback_query.data.split('_')[1]
    user_data = await state.get_data()
    action = user_data.get('action')
    if action == 'add_accounts':
        await state.update_data(country=country)
        await bot.edit_message_text("Загрузите файл с аккаунтами в формате .txt или отправьте текстовое сообщение с аккаунтами:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_back_keyboard())
        await Form.file_upload.set()
    elif action == 'get_accounts':
        await state.update_data(country=country)
        await bot.edit_message_text("Укажите количество аккаунтов, которые вы хотите получить:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_number_keyboard())
        await Form.number_of_accounts.set()
    elif action == 'delete_country':
        db.delete_country(country)
        await bot.edit_message_text(f"Страна '{country}' удалена.", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_back_keyboard())
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'new_country', state=Form.country)
async def new_country(callback_query: types.CallbackQuery):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    await Form.new_country.set()
    await bot.edit_message_text("Введите название новой страны:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_back_keyboard())

@dp.message_handler(state=Form.new_country)
async def handle_new_country(message: types.Message, state: FSMContext):
    if not is_allowed_user(message.from_user.id):
        await message.reply("У вас нет доступа к этому боту.")
        return
    new_country = message.text
    db.add_country(new_country)
    await state.update_data(country=new_country)
    await Form.action.set()
    await message.reply(f"Страна '{new_country}' добавлена. Выберите действие:", reply_markup=get_main_keyboard())

@dp.message_handler(state=Form.file_upload, content_types=['document', 'text'])
async def handle_accounts_file_or_text(message: types.Message, state: FSMContext):
    if not is_allowed_user(message.from_user.id):
        await message.reply("У вас нет доступа к этому боту.")
        return
    user_data = await state.get_data()
    country = user_data.get('country')
    if message.content_type == 'document':
        document = message.document
        if document.mime_type == 'text/plain':
            file = await bot.download_file_by_id(document.file_id)
            accounts = file.read().decode('utf-8').splitlines()
            await state.update_data(accounts=accounts)
            await bot.send_message(message.chat.id, "Выберите формат аккаунтов:", reply_markup=get_formats_keyboard(include_delete_format=False))
            await Form.account_format.set()
        else:
            await message.reply("Неверный формат файла. Пожалуйста, загрузите файл в формате .txt.")
    elif message.content_type == 'text':
        accounts = message.text.splitlines()
        await state.update_data(accounts=accounts)
        await bot.send_message(message.chat.id, "Выберите формат аккаунтов:", reply_markup=get_formats_keyboard(include_delete_format=False))
        await Form.account_format.set()

@dp.callback_query_handler(lambda c: c.data == 'add_format', state=[Form.account_format, Form.manage_formats])
async def add_format(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    await Form.new_format.set()
    await bot.edit_message_text("Введите новый формат (например, email|emailpass|login|pass|reftoken|clientid):", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_back_keyboard())

@dp.message_handler(state=Form.new_format)
async def handle_new_format(message: types.Message, state: FSMContext):
    if not is_allowed_user(message.from_user.id):
        await message.reply("У вас нет доступа к этому боту.")
        return
    new_format = message.text
    required_fields = ["email", "emailpass", "login", "pass", "reftoken", "clientid"]
    if all(field in new_format for field in required_fields):
        db.add_format(new_format)
        await message.reply(f"Формат '{new_format}' успешно добавлен.", reply_markup=get_formats_keyboard(include_delete_format=False))
        await Form.account_format.set()
    else:
        await message.reply(f"Формат '{new_format}' не содержит все необходимые поля (email, emailpass, login, pass, reftoken, clientid).", reply_markup=get_back_keyboard())
        await Form.account_format.set()

@dp.callback_query_handler(lambda c: c.data.startswith('format_'), state=Form.account_format)
async def handle_account_format(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    account_format = callback_query.data.split('_')[1]
    user_data = await state.get_data()
    country = user_data.get('country')
    accounts = user_data.get('accounts')
    for account in accounts:
        db.add_account(country, account, account_format)
    await bot.edit_message_text(f"Аккаунты успешно добавлены в страну '{country}'.", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_main_keyboard())
    await state.finish()
    await send_welcome(callback_query.message)

@dp.callback_query_handler(lambda c: c.data.startswith('number_'), state=Form.number_of_accounts)
async def handle_number_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    number = int(callback_query.data.split('_')[1])
    user_data = await state.get_data()
    country = user_data.get('country')
    accounts = db.get_accounts(country, number)
    response = '\n'.join(accounts) or "Нет доступных аккаунтов."
    await bot.send_message(callback_query.from_user.id, response, reply_markup=get_main_keyboard())
    await state.finish()
    await send_welcome(callback_query.message)

@dp.callback_query_handler(lambda c: c.data == 'custom_number', state=Form.number_of_accounts)
async def handle_custom_number(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    await Form.custom_number.set()
    await bot.edit_message_text("Введите количество аккаунтов:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_back_keyboard())

@dp.message_handler(state=Form.custom_number)
async def handle_custom_number_input(message: types.Message, state: FSMContext):
    if not is_allowed_user(message.from_user.id):
        await message.reply("У вас нет доступа к этому боту.")
        return
    number_of_accounts = int(message.text)
    user_data = await state.get_data()
    country = user_data.get('country')
    accounts = db.get_accounts(country, number_of_accounts)
    response = '\n'.join(accounts) or "Нет доступных аккаунтов."
    await message.reply(response, reply_markup=get_main_keyboard())
    await state.finish()
    await send_welcome(message)

@dp.callback_query_handler(lambda c: c.data == 'back_to_main', state='*')
async def back_to_main(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    await state.finish()
    await Form.action.set()
    await bot.edit_message_text("Привет! Я бот для управления аккаунтами. Выберите действие:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_main_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'back_to_admin', state=[Form.manage_formats, Form.new_format, Form.delete_format])
async def back_to_admin(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    await bot.edit_message_text("Панель администратора:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_admin_keyboard())
    await Form.admin_panel.set()

@dp.callback_query_handler(lambda c: c.data in ['total_accounts', 'delete_all_accounts', 'stats', 'account_info', 'manage_formats'], state=Form.admin_panel)
async def handle_admin_actions(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    action = callback_query.data
    if action == 'total_accounts':
        total = db.get_total_accounts()
        await bot.edit_message_text(f"Общее кол-во аккаунтов: {total}", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_admin_keyboard())
    elif action == 'delete_all_accounts':
        await Form.confirm_delete_all.set()
        await bot.edit_message_text("Вы уверены, что хотите удалить все аккаунты? Это действие необратимо. [Да/Нет]", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_back_keyboard())
    elif action == 'stats':
        stats = db.get_stats()
        await bot.edit_message_text(f"Статистика:\n{stats}", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_admin_keyboard())
    elif action == 'account_info':
        response = ""
        countries = db.get_countries()
        for country in countries:
            country_name = country[1]
            account_dates = db.get_account_dates(country_name)
            if account_dates:
                response += (
                    f"Страна: {country_name}\n"
                    f"Первое пополнение: {account_dates['first_added']} (дней назад: {account_dates['days_since_first']}, часов назад: {account_dates['hours_since_first']})\n"
                    f"Последнее пополнение: {account_dates['last_added']} (дней назад: {account_dates['days_since_last']}, часов назад: {account_dates['hours_since_last']})\n"
                    "------------------------------\n"
                )
        try:
            await bot.edit_message_text(response or "Нет доступной информации о пополнениях.", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_admin_keyboard())
        except aiogram.utils.exceptions.MessageNotModified:
            pass
    elif action == 'manage_formats':
        await Form.manage_formats.set()
        await bot.edit_message_text("Управление форматами:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_formats_keyboard(include_delete_format=True))

@dp.message_handler(lambda message: message.text.lower() in ['да', 'нет'], state=Form.confirm_delete_all)
async def confirm_delete_all(message: types.Message, state: FSMContext):
    if not is_allowed_user(message.from_user.id):
        await message.reply("У вас нет доступа к этому боту.")
        return
    if message.text.lower() == 'да':
        db.delete_all_accounts()
        await message.reply("Все аккаунты удалены.", reply_markup=get_admin_keyboard())
    else:
        await message.reply("Операция отменена.", reply_markup=get_admin_keyboard())
    await Form.admin_panel.set()

@dp.callback_query_handler(lambda c: c.data == 'delete_format', state=Form.manage_formats)
async def delete_format(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    await Form.delete_format.set()
    await bot.edit_message_text("Выберите формат для удаления:", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_formats_keyboard(include_delete_format=True))

@dp.callback_query_handler(lambda c: c.data.startswith('format_'), state=Form.delete_format)
async def handle_delete_format(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_allowed_user(callback_query.from_user.id):
        await bot.send_message(callback_query.from_user.id, "У вас нет доступа к этому боту.")
        return
    format_to_delete = callback_query.data.split('_')[1]
    db.delete_format(format_to_delete)
    await bot.edit_message_text(f"Формат '{format_to_delete}' успешно удален.", callback_query.from_user.id, callback_query.message.message_id, reply_markup=get_formats_keyboard(include_delete_format=True))
    await Form.manage_formats.set()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
