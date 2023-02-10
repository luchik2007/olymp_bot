import asyncio
import datetime
import aioschedule as aioschedule
import keyboards as kb
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode, ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.utils.markdown import text, italic, code
from config import TOKEN, SUBJECTS, OLYMP_LEVELS, REMIND_TIME, PROCESS_TIME, CLEAN_TIME
from fizteh.db import get_olymp_data, set_scheduler_data, get_scheduler_data, get_olymp, set_schedule_inactive
from fizteh2.db import clean_inactive_schedule

# Инициализация бота
bot = Bot(token=TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)

# Создадим пулы для выборки и обработки добавления напоминаний
proc_data = {}  # пул хранения данных для выборки
query_data = {}  # пул хранения для добавления напоминания


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
    user_chat_id = callback_query.from_user.id
    school_class = callback_query.data[6:]  # получим номер класса
    # заполняем пул для запроса с привязкой к ID пользователя
    if user_chat_id in proc_data.values():
        proc_data[user_chat_id]['school_class'] = school_class
    else:
        proc_data[user_chat_id] = {}
        proc_data[user_chat_id]['is_active'] = 1
        proc_data[user_chat_id]['school_class'] = school_class
    print(proc_data)  # TODO !!! Для наглядности отладки. Потом убрать
    # Выводим текст и клавиатуру школьных предметов
    await bot.send_message(callback_query.from_user.id,
                           f'Выбран - {school_class} класс. Выберите предмет олимпиады из предложенных',
                           reply_markup=kb.subject_btn_full)


# обработка выбора предмета олимпиады
@dp.callback_query_handler(lambda c: c.data.startswith('subj'))
async def process_subj_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_chat_id = callback_query.from_user.id
    subject = callback_query.data[5:]  # Получаем код школьного предмета
    proc_data[user_chat_id]['subject'] = subject  # Добавляем в пул запроса предмет
    print(proc_data)  # TODO !!! Для наглядности отладки. Потом убрать
    # Выводим текст и клавиатуру уровней школьных олимпиад
    await bot.send_message(callback_query.from_user.id,
                           f'Вами был выбран предмет - {SUBJECTS[subject]}. Выберите уровень олимпиады из предложенных',
                           reply_markup=kb.level_btn_full)


# обработка уровня олимпиады
@dp.callback_query_handler(lambda c: c.data.startswith('level'))
async def process_level_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_chat_id = callback_query.from_user.id
    olymp_level = callback_query.data[6:]  # Получаем уровень олимпиады и выводим результаты
    proc_data[user_chat_id]['olymp_level'] = olymp_level
    print(proc_data)  # TODO !!! Для наглядности отладки. Потом убрать
    await bot.send_message(callback_query.from_user.id,
                           f'Вами был выбран уровень олимпиады - {OLYMP_LEVELS[olymp_level]}. Вывожу подходящие '
                           f'варианты:')


# добавление напоминания об олимпиаде
@dp.callback_query_handler(lambda c: c.data.startswith('reminder'))
async def process_reminder_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    que_number = int(callback_query.data[9:])  # получим номер в выборке

    # получим все данные для напоминания и сохраним его в БД
    user_id = callback_query.from_user.id
    olymp = query_data[user_id][que_number]
    print('Добавляю напоминание', olymp)   # TODO !!! Для наглядности отладки. Потом убрать
    olymp_id = olymp['id']
    olymp_date = olymp['date']
    olymp_name = olymp['name']
    # TODO !!! Для наглядности отладки. Потом убрать
    print(f'Данные: user_id = {user_id}, olymp_id = {olymp_id}, olymp_date = {olymp_date}, olymp_name = {olymp_name}')

    # получим даты за 7, 3 и 1 день до олимпиады, чтобы потом не грузить БД вычислениями на ходу
    date_rem_7 = datetime.date.fromisoformat(olymp_date) - datetime.timedelta(7)
    date_rem_3 = datetime.date.fromisoformat(olymp_date) - datetime.timedelta(3)
    date_rem_1 = datetime.date.fromisoformat(olymp_date) - datetime.timedelta(1)

    # добавим напоминания на 1,3,7 дней в БД
    set_scheduler_data(user_id, olymp_id, date_rem_7)
    set_scheduler_data(user_id, olymp_id, date_rem_3)
    set_scheduler_data(user_id, olymp_id, date_rem_1)

    await bot.send_message(user_id,
                           f'Добавлено напоминание по олимпиаде - \"{olymp_name}\". Вы получите напоминание за '
                           f'7, 3 и 1 день до олимпиады.')


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
        value_date = datetime.date.fromisoformat(value['olymp_date'])
        # если текущая дата >= даты напоминания, то посылаем сообщение
        if today >= value_date:
            scheduler_id = value['scheduler_id']
            user_id = value['user_id']
            olymp_id = value['olymp_id']
            olymp = get_olymp(olymp_id)
            olymp_name = olymp['name']
            olymp_date = olymp['date']
            await bot.send_message(user_id,
                                   f'Напоминаем, что олимпиада \"{olymp_name}\" состоится {olymp_date}. Не забудьте проверить корректность документов')
            set_schedule_inactive(scheduler_id)  # После обработки делаем напоминание неактивным


# Удаление неактивных напоминаний, чтобы не захламлять БД
async def clean_reminds():
    clean_inactive_schedule()


# # Обработка формирования запроса
@dp.message_handler()
async def process_request():
    # Выполняем запрос по параметрам если есть данные для обработки
    if len(proc_data) != 0:
        data_to_delete = []
        for value in proc_data:
            items = proc_data[value]
            if items.get('school_class', 0) != 0 and items.get('subject', 0) != 0 and items.get('olymp_level',
                                                                                                0) != 0 and items.get(
                'is_active', 0) == 1:
                query_result = get_olymp_data(items['school_class'], items['subject'], items['olymp_level'])
                query_data[value] = query_result
                print(query_data)
                # Проверяем результат выполнения запроса. Если не пуст, то обрабатываем
                if len(query_result) == 0:
                    await bot.send_message(value, 'К сожалению по вашему запросу ничего не найдено! '
                                                  'Пожалуйста, попробуйте сделать новый запрос')
                else:
                    for i, item in enumerate(query_result):
                        # Выводим кнопки напоминания
                        reminder_btn_full = InlineKeyboardMarkup()
                        reminder_btn = InlineKeyboardButton('Добавить напоминание', callback_data=f'reminder_{i}')
                        reminder_btn_full.add(reminder_btn)
                        # Выводим основную информацию по олимпиаде
                        await bot.send_message(value,
                                               f"=====================\n"
                                               f"Название: {item['name']}\n"
                                               f"URL: {item['url']}\n"
                                               f"Дата: {item['date']}\n"
                                               f"=====================\n",
                                               reply_markup=reminder_btn_full)
                data_to_delete.append(value)
        # чистим временные пулы после прохождения обработки
        for value in data_to_delete:
            del proc_data[value]
        data_to_delete.clear()


# Устанавливаем планировщик
async def scheduler():
    aioschedule.every(PROCESS_TIME).seconds.do(process_request)  # Обработка поступающих запросов пользователей
    aioschedule.every().day.at(REMIND_TIME).do(send_reminds)  # Отправка напоминаний по олимпиадам
    aioschedule.every().day.at(CLEAN_TIME).do(clean_reminds)  # Удаление неактивных напоминаний из БД
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(2)


# Старт планировщика
async def on_startup(dp):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
