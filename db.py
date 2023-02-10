import sqlite3

from fizteh.config import SUBJECTS

db_name = 'olymp.sqlite'
con = sqlite3.connect(db_name)  # устанавливаем соединение
cur = con.cursor()  # курсор


# запрос на получение данных об олимпиадах по пользовательскому запросу
def get_olymp_data(school_class, subject, level):
    # сформируем базовый запрос
    que = f"""
        SELECT name, url, date, id
        FROM olymp2
        WHERE 1 = 1 
           AND class = {school_class}
           AND subject = "{SUBJECTS[subject]}"    
        """
    # если уровень из перечня, то добавляем это условие в запрос
    if level in ('1', '2', '3'):
        que += f"""  AND level = "{level}" """
    result = cur.execute(que).fetchall()
    # сохраним результаты в список словарей
    final_result = [{'name': value[0], 'url': value[1], 'date': value[2], 'id': value[3]} for value in result]
    return final_result


# добавляем запись в напоминания
def set_scheduler_data(user_id, olymp_id, olymp_date):
    que = f"""
        INSERT INTO reminder(user_id, olymp_id, olymp_date, is_active)
        VALUES ('{user_id}', '{olymp_id}', '{olymp_date}', '1')    
        """
    cur.execute(que)
    con.commit()


# получаем все активные записи напоминаний
def get_scheduler_data(date):
    # сформируем базовый запрос
    que = f"""
        SELECT user_id, olymp_id, id, olymp_date
        FROM reminder
        WHERE 1 = 1 
           AND is_active = '1'
        """
    result = cur.execute(que).fetchall()
    final_result = [{'user_id': value[0], 'olymp_id': value[1], 'scheduler_id': value[2], 'olymp_date': value[3]} for
                    value in result]
    return final_result


# получаем информацию по олимпиаде по ее ID
def get_olymp(olymp_id):
    # сформируем базовый запрос
    que = f"""
        SELECT name, date
        FROM olymp2
        WHERE 1 = 1 
           AND id = {olymp_id}    
        """
    value = cur.execute(que).fetchone()
    final_result = {'name': value[0], 'date': value[1]}
    return final_result


# Делаем напоминание неактивным
def set_schedule_inactive(scheduler_id):
    que = f"""
        UPDATE reminder
        SET is_active = '0'
        WHERE 1 = 1 
           AND id = {scheduler_id}    
        """
    cur.execute(que)
    con.commit()


# Удаляем неактивные напоминания
def clean_inactive_schedule():
    que = f"""
        DELETE FROM reminder
        WHERE 1 = 1 
           AND is_active = 0    
        """
    cur.execute(que)
    con.commit()
