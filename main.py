import requests.exceptions
import telebot
import pprint
import time
import sqlite3
while True:
    try:
        con = sqlite3.connect('bot.db', check_same_thread=False)
        cur = con.cursor()

        bot = telebot.TeleBot('')


        def gen_id(table_name, column):
            a = list(map(lambda x: x[0], cur.execute(f'''SELECT {column} from {table_name}''').fetchall()))
            print('a', a)
            try:
                result = max(a) + 1
                print('b', result)
            except ValueError:
                print('WGWR')
                return 1
            return result


        @bot.message_handler(commands=['start'])
        def start_message(message):
            username = message.from_user.username
            user_id = message.from_user.id
            # if use
            cur.execute(f'''INSERT INTO users VALUES ("{username}", {user_id})''')
            con.commit()
            bot.reply_to(message, 'Данные успешно добавлены! Вы можете работать с ботом!')


        @bot.message_handler(commands=['new_debt'])
        def new_debt(message):
            debt_id = gen_id('debts', 'debt_id')
            chat = message.chat
            sender = message.from_user
            collector_id = sender.id
            result = cur.execute(f'''SELECT collector_id FROM collector WHERE collector_id={collector_id}''').fetchone()
            cur.execute(f'''INSERT INTO collector VALUES({collector_id}, "{sender.username}", {debt_id})''')
            text = message.text.split('\n')
            out = None
            try:
                pprint.pprint(text)
                if text[1].lower() == 'должники:':
                    result = cur.execute(f'''SELECT chat_id FROM groups WHERE chat_id={chat.id}''').fetchone()
                    print('chat_id', result)
                    if not result:
                        cur.execute(f'''INSERT INTO groups(chat_name, chat_id) VALUES ("{chat.title}", {chat.id})''')
                        con.commit()
                    do_out = True
                    for i in text[2:]:
                        print(text[2:], i[0] == '@')
                        name, n = i.split('-')
                        debtor_id = cur.execute(f'''SELECT debtor_id FROM debtors WHERE debtor="{name[1:]}"''').fetchone()
                        con.commit()
                        print(debtor_id)
                        if not debtor_id:
                            debtor_id = cur.execute(f'''SELECT user_id FROM users WHERE username="{name[1:]}"''').fetchone()
                            if not debtor_id:
                                bot.reply_to(message, f'''Пользователь {name} не добавлен в базу данных!
        Он должен прописать команду /start''')
                                do_out = False
                                continue
                        else:
                            debtor_id = debtor_id[0]
                        print(debtor_id)
                        if type(debtor_id) == tuple:
                            debtor_id = debtor_id[0]
                        cur.execute(f'''INSERT OR IGNORE INTO debtors VALUES({debt_id}, "{name[1:]}", {debtor_id}, {n})''')
                        con.commit()
                    debt_name = text[0][len(text[0].split()[0]):]
                    if do_out:
                        cur.execute(f'''INSERT INTO debts VALUES({collector_id}, "{debt_name}", {chat.id}, {debt_id})''')
                        bot.send_message(chat.id, 'Долги успешно посчитаны!')
                        con.commit()
                    else:
                        bot.send_message(chat.id, 'Команда введена неправильно! Проверьте написание командой "/help"')
            except IndexError:
                bot.send_message(chat.id, 'Команда введена неправильно! Проверьте написание командой "/help"')


        @bot.message_handler(commands=['my_debtors'])
        def my_debtors(message):
            debt_id = cur.execute(f'''SELECT debt_id FROM collector WHERE collector_id={message.from_user.id}''').fetchall()
            was = []
            result = []
            for i in debt_id:
                i = i[0]
                if i not in was:
                    was.append(i)
                    a = list(map(lambda x: x[0], cur.execute(f'''SELECT debt_id FROM debts WHERE chat_id={message.chat.id}''').fetchall()))
                    print(a)
                    if i in a:
                        result.extend(cur.execute(f'''SELECT debtor, debt_n FROM debtors WHERE debt_id={i}''').fetchall())

            text = []
            for name, n in result:
                text.append(f'''@{name} - {n}''')
            if text:
                bot.reply_to(message, '\n'.join(text))
            else:
                bot.reply_to(message, 'У вас нет должников')


        @bot.message_handler(commands=['my_debts'])
        def my_debts(message):
            chat = message.chat
            user = message.from_user
            result = cur.execute(f'''SELECT * FROM debtors WHERE debtor_id={user.id}''').fetchall()
            print(result)
            if not result:
                bot.send_message(chat.id, f'{user.first_name.capitalize()}, у вас нет долгов!')
            else:
                for i in result:
                    print(i)
                    text = []
                    debt_id, debtor_name, debtor_id, debt_n = i
                    collector_id = cur.execute(f'''SELECT collector_id FROM collector WHERE debt_id={debt_id}''').fetchone()
                    collector = cur.execute(f'''SELECT collector_name FROM collector WHERE collector_id={collector_id[0]}''').fetchone()
                    debt_name = cur.execute(f'''SELECT debt_name FROM debts WHERE debt_id={debt_id}''').fetchone()
                    a = list(map(lambda x: x[0], cur.execute(f'''SELECT debt_id FROM debts WHERE chat_id={message.chat.id}''')))
                    if debt_id in a:
                        text.append(f'Долг "{debt_name[0]}" для "@{collector[0]}" - {debt_n}')
                    if text:
                        bot.reply_to(message, '\n'.join(text))
                    else:
                        bot.reply_to(message, 'У вас нет долгов!')


        @bot.message_handler(commands=['help'])
        def help(message):
            bot.reply_to(message, 'Инструкция по вводу команды /new_debt\n'
                                  '/new_debt <Название долга>\n'
                                  'Должники:\n'
                                  '@<username>-<сумма долга>')




        bot.polling(none_stop=True)
    except requests.exceptions.ReadTimeout:
        pass