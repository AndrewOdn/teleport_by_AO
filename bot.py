# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import pytz
from pyrogram import Client, Filters, Message

from extractor import apply_emoji_filter, extract_from_text, \
    save_today_actual_xls, delete_extract_container_folder, get_extra_words
from settings import USER_NAME, API_ID, API_HASH, DATE_WITH_TIME_FORMAT, HANDLED_CHATS

EXTRA_WORDS = get_extra_words()
logging.basicConfig(filename='logs/%s.txt' % datetime.today().strftime(DATE_WITH_TIME_FORMAT)
                    , level=logging.INFO
                    , format='[%(asctime)s:%(levelname)s]: %(message)s'
                    , datefmt='%Y-%m-%d %H:%M:%S')
app = Client(USER_NAME, api_id=API_ID, api_hash=API_HASH)
def get_hadled_chats():
    for i in app.get_dialogs():
        HANDLED_CHATS.append(i['chat']['id'])
def get_chat_name(message: Message) -> str:
    first_name = message.chat.first_name
    if first_name:
        return first_name
    else:
        title = message.chat.title
        if title:
            return title
        else:
            forward_sender = message.forward_sender_name
            if forward_sender:
                return forward_sender
            else:
                return '*chat name not found*'


def extractor_from_message(message: Message) -> list:
    try:
        text = message.text
        if not text:
            text = message.caption
            if not text:
                raise Exception('Message without text')
        """Нужено конвертнут ьсообщение в такоую вот строчку"""
        #s = [['Redmi Note 10T 128Gb Silver', 17250], ['Redmi Note 10T 128Gb Silver', 18250], ['Redmi Note 10T 128Gb Silver', 19250]]
        return extract_from_text(
            apply_emoji_filter(text)
        )
    except Exception as e:
        logging.exception(e)
        return []


def force_in_mem_update_today_extract_for_chat(chat_id):
    today_date = datetime.utcnow().date()
    delete_extract_container_folder(chat_id)
    today_extract = []
    for message in app.iter_history(chat_id):
        if datetime.utcfromtimestamp(message.date).date() == today_date:
            today_extract.extend(extractor_from_message(message))
        else:
            break
    save_today_actual_xls(today_extract, chat_id)


def get_msk_formatted_time(datetime) -> str:
    moscow_tz = pytz.timezone('Europe/Moscow')
    edit_time = datetime.fromtimestamp(datetime, tz=moscow_tz)
    return edit_time.strftime('%m-%d %H:%M:%S')


def force_in_mem_today_actual_for_all(handled_chat):
    print('Today all started')
    logging.info('Today all started')
    if handled_chat == -1:
        for handled_chat_id in HANDLED_CHATS:
            print(handled_chat_id)
            logging.info('Today %s started' % handled_chat_id)
            try:
                force_in_mem_update_today_extract_for_chat(handled_chat_id)

            except Exception as e:
                logging.exception(e)
    else:
        print(handled_chat)
        logging.info('Today %s started' % handled_chat)
        try:
            force_in_mem_update_today_extract_for_chat(handled_chat)
        except Exception as e:
            logging.exception(e)
    print('Today all finish')
    logging.info('Today all finish')


@app.on_deleted_messages()
def on_messages_delete(client, messages):
    if len(messages) > 0:
        force_in_mem_today_actual_for_all()


@app.on_message(Filters.edited)
def on_message_edited(client, message):
    chat_id = message.chat.id
    if chat_id in HANDLED_CHATS:
        users = HANDLED_CHATS[chat_id]
        for to in users:
            try:
                if to == chat_id:
                    forwarded_message = message
                else:
                    forwarded_message = message.forward(chat_id=to, as_copy=True)
                forwarded_message.reply_text('Изменено в "%s"' % get_msk_formatted_time(message.edit_date))
            except:
                logging.error('Error when forward to %s' % to)
        if datetime.utcfromtimestamp(message.date).date() == datetime.today().date():
            force_in_mem_today_actual_for_all()


@app.on_message()
def on_message(client, message):
    chat_id = message.chat.id
    if not message.empty:
        print('Новое сообщение из "%s"' % get_chat_name(message))
        #forwarded_message.reply_text('Новое сообщение из "%s"' % get_chat_name(message))
        force_in_mem_today_actual_for_all(chat_id)


def main():
    app.start()
    get_hadled_chats()
    force_in_mem_today_actual_for_all(-1)
    Client.idle()
    app.stop()


if __name__ == '__main__':
    main()
