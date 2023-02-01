import asyncio
import datetime

import aioschedule as aioschedule
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode, ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.utils.markdown import text, italic, code
import keyboards as kb

from config import TOKEN, SUBJECTS, OLYMP_LEVELS, REMIND_TIME, REMIND_DAYS
from fizteh.db import get_olymp_data, set_scheduler_data, get_scheduler_data, get_olymp, set_schedule_inactive

# Инициализация бота
bot = Bot(token=TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)

# Блок переменных для выборки из БД
school_class = ''  # класс школьника, используется для фильтрации
olymp_level = ''  # уровень олимпиады
subject = ''  # предмет
query_result = ''  # результат выполнения запроса


# Обработка команды <start>
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.answer(f"Привет, {message.from_user.full_name}!\nЯ - бот, предназначенный для информирования по "
                         f"олимпиадам. Я могу вывести для тебя информацию по интересующему предмету и добавить "
                         f"напоминание, чтобы ты не забыл про олимпиаду)")
    # Выводим сообщение и клавиатуру классов учащихся
    await message.answer("Пожалуйста, выбери класс обучения из предложенных", reply_markup=kb.class_btn_full)


# Обработка команды <help>
@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Для начала работы с ботом набери - /start")


# обработка выбора класса
@dp.callback_query_handler(lambda c: c.data.startswith('class'))
async def process_class_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    global school_class
    school_class = callback_query.data[6:]  # получим номер класса
    # Выводим текст и клавиатуру школьных предметов
    await bot.send_message(callback_query.from_user.id,
                           f'Выбран - {school_class} класс. Выберите предмет олимпиады из предложенных',
                           reply_markup=kb.subject_btn_full)


# обработка выбора предмета олимпиады
@dp.callback_query_handler(lambda c: c.data.startswith('subj'))
async def process_subj_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    global subject
    subject = callback_query.data[5:]  # Получаем код школьного предмета
    # Выводим текст и клавиатуру уровней школьных олимпиад
    await bot.send_message(callback_query.from_user.id,
                           f'Вами был выбран предмет - {SUBJECTS[subject]}. Выберите уровень олимпиады из предложенных',
                           reply_markup=kb.level_btn_full)


# обработка уровня олимпиады
@dp.callback_query_handler(lambda c: c.data.startswith('level'))
async def process_level_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    global olymp_level
    olymp_level = callback_query.data[6:]  # Получаем уровень олимпиады и выводим результаты
    await bot.send_message(callback_query.from_user.id,
                           f'Вами был выбран уровень олимпиады - {OLYMP_LEVELS[olymp_level]}. Вывожу подходящие '
                           f'варианты:')

    # Выполняем запрос по параметрам
    global query_result
    query_result = get_olymp_data(school_class, subject, olymp_level)
    # Проверяем результат выполнения запроса. Если не пуст, то обрабатываем
    if len(query_result) == 0:
        await bot.send_message(callback_query.from_user.id, 'К сожалению по вашему запросу ничего не найдено! '
                                                            'Пожалуйста, попробуйте сделать новый запрос')
    else:
        for i, item in enumerate(query_result):
            # Выводим кнопки напоминания
            reminder_btn_full = InlineKeyboardMarkup()
            reminder_btn = InlineKeyboardButton('Добавить напоминание', callback_data=f'reminder_{i}')
            reminder_btn_full.add(reminder_btn)
            # Выводим основную информацию по олимпиаде
            await bot.send_message(callback_query.from_user.id,
                                   f"=====================\n"
                                   f"Название: {item['name']}\n"
                                   f"URL: {item['url']}\n"
                                   f"Дата: {item['date']}\n"
                                   f"=====================\n",
                                   reply_markup=reminder_btn_full)


# добавление напоминания об олимпиаде
@dp.callback_query_handler(lambda c: c.data.startswith('reminder'))
async def process_reminder_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    que_number = int(callback_query.data[9:])  # получим номер в выборке

    # получим все данные для напоминания и сохраним его в БД
    user_id = callback_query.from_user.id
    olymp = query_result[que_number]
    olymp_id = olymp['id']
    olymp_date = olymp['date']
    olymp_name = olymp['name']

    set_scheduler_data(user_id, olymp_id, olymp_date)  # Сохраним напоминание в БД
    await bot.send_message(user_id,
                           f'Добавлено напоминание по олимпиаде - \"{olymp_name}\". Вы получите напоминание за '
                           f'{REMIND_DAYS} дней до олимпиады.')


# Обработка неизвестных действий или команд
@dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(msg: types.Message):
    message_text = text('Я не знаю, что с этим делать ',
                        italic('\nЯ просто напомню,'), 'что есть',
                        code('команда'), '/help')
    await msg.reply(message_text, parse_mode=ParseMode.MARKDOWN)


# Обработка напоминаний
@dp.message_handler()
async def send_reminds():
    # Получим текущую дату и выберем все активные напоминания
    today = datetime.date.today()
    result = get_scheduler_data(today)
    # Обработаем активные напоминания
    for value in result:
        # дата, начиная с которой необходимо напоминать
        value_date = datetime.date.fromisoformat(value['olymp_date']) - datetime.timedelta(days=REMIND_DAYS)
        # если текущая дата >= даты напоминания, то посылаем сообщение
        if today >= value_date:
            scheduler_id = value['scheduler_id']
            user_id = value['user_id']
            olymp_id = value['olymp_id']
            olymp = get_olymp(olymp_id)
            olymp_name = olymp['name']
            olymp_date = olymp['date']
            await bot.send_message(user_id, f'Напоминаем, что олимпиада \"{olymp_name}\" состоится {olymp_date}')
            set_schedule_inactive(scheduler_id)  # После обработки делаем напоминание неактивным


# Устанавливаем планировщик
async def scheduler():
    aioschedule.every().day.at(REMIND_TIME).do(send_reminds)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(30)


# Старт планировщика
async def on_startup(dp):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
