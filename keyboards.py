from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Здесь содержатся клавиатуры выбора бота

# Зададим кнопки для школьных классов и добавим их на общую клавиатуру выбора
class_btn_8 = InlineKeyboardButton('8 класс', callback_data='class_8')
class_btn_9 = InlineKeyboardButton('9 класс', callback_data='class_9')
class_btn_10 = InlineKeyboardButton('10 класс', callback_data='class_10')
class_btn_11 = InlineKeyboardButton('11 класс', callback_data='class_11')
class_btn_full = InlineKeyboardMarkup(row_width=2)
class_btn_full.add(class_btn_8, class_btn_9, class_btn_10, class_btn_11)

# Зададим кнопки уровня олимпиады и добавим их на общую клавиатуру выбора
level_btn_1 = InlineKeyboardButton('1 уровень', callback_data='level_1')
level_btn_2 = InlineKeyboardButton('2 уровень', callback_data='level_2')
level_btn_3 = InlineKeyboardButton('3 уровень', callback_data='level_3')
level_btn_any = InlineKeyboardButton('Любой', callback_data='level_any')
level_btn_full = InlineKeyboardMarkup(row_width=2)
level_btn_full.add(level_btn_1, level_btn_2, level_btn_3, level_btn_any)

# Зададим кнопки для предметов и добавим их на общую клавиатуру выбора
subject_btn_1 = InlineKeyboardButton('Физика', callback_data='subj_physics')
subject_btn_2 = InlineKeyboardButton('Математика', callback_data='subj_math')
subject_btn_3 = InlineKeyboardButton('Информатика', callback_data='subj_comp_science')
subject_btn_4 = InlineKeyboardButton('Химия', callback_data='subj_chemistry')
subject_btn_5 = InlineKeyboardButton('Русский язык', callback_data='subj_russian')
subject_btn_6 = InlineKeyboardButton('Экономика', callback_data='subj_economics')
subject_btn_7 = InlineKeyboardButton('История', callback_data='subj_history')
subject_btn_8 = InlineKeyboardButton('Биология', callback_data='subj_biology')
subject_btn_full = InlineKeyboardMarkup(row_width=2)
subject_btn_full.add(subject_btn_1, subject_btn_2, subject_btn_3, subject_btn_4, subject_btn_5, subject_btn_6,
                     subject_btn_7, subject_btn_8)
