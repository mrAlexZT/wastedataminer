# -*- coding: utf-8 -*-
from telegram import (ReplyKeyboardMarkup,ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
import time
import logging
import codecs
import csv
from config import TOKEN
import uuid
import os
import requests
import json
import http.client as http_client
from transliterate import translit

http_client.HTTPConnection.debuglevel = 1

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

logger = logging.getLogger(__name__)

PHOTO, CHOOSING, REPEAT = range(3)

def make_keyboard(columns):
    i = 0
    reply_keyboard = []
    tmp_keyboard = []
    with codecs.open('recycle_db.csv', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        i = 0
        for row in reader:
            if row[1] != 'item':
                i += 1
                tmp_keyboard.append(row[1])
                if i >= columns:
                    reply_keyboard.append(tmp_keyboard)
                    tmp_keyboard = []
                    i = 0
    reply_keyboard.append(['cancel'])
    return reply_keyboard

reply_keyboard = make_keyboard(2)

def start(bot, update):
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=update.message.chat.id,
                    text="Загрузите изображение!",
                   reply_markup=reply_markup)
    return PHOTO

_URL_API_ = "http://127.0.0.1:5001/api/UploadFile4Learning"
_FILE_4_LEARN_ = "files"

def custom_choice(bot, update, user_data):
    text = update.message.text
    user_data['choice'] = text
    file_name = user_data['filename'].replace("--", "-" + translit(user_data['choice'], reversed=True) + "-")
    print (file_name)
    print (user_data['filename'])
    os.rename(user_data['filename'], file_name)

    # попытка вызвать сервис и передать картинку для обучения.
    print ("start sending")
    logger.info("start sending")
    try:
        print (file_name)
        files = {'file': (open(file_name,'rb'), 'image/jpeg', {'Expires': '0'})}
        print("001")
        data = {'user_id': update.message.from_user.id,
                'source': 'bot',
                'filename': file_name.split('/')[1],
                'descr': user_data['choice']}
        print("002")
        print("files:", files, "data:", data)
        req = requests.post(url=_URL_API_, files=files, data=data)
        
        print("003")
        print("Request:", req, req.text, req.content)
        
    except Exception as ex:
        print (ex)
        print("004")
    print('-'*10)
    print("005")
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=update.message.chat.id,
                    text="Превосходно! Спасибо за предоставленное изображение!",
                   reply_markup=reply_markup)
    del user_data['choice']
    del user_data['filename']
    bot.sendMessage(chat_id=update.message.chat.id,
                    text="Вы хотите загрузить еще изображение? [Да / Нет]",
                    reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]]))
    return REPEAT

def photo(bot, update, user_data):
    if not os.path.exists('files'):
        os.mkdir('files')
    text = user_data['choice']=""
    user = update.message.from_user
    f = bot.getFile(update.message.photo[-1].file_id)

    if not os.path.exists(_FILE_4_LEARN_):
        os.makedirs(_FILE_4_LEARN_)
    
    fn = _FILE_4_LEARN_+"/{}-{}-{}-{}.jpg".format(user.id,text,time.time(),'001')
    f.download(fn)
    user_data['filename']=fn
    update.message.reply_text(
        'Укажите, что это за категория отходов:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSING

def skip_photo(bot, update):
    user = update.message.from_user
    logger.info("User %s did not send a photo." % user.first_name)
    update.message.reply_text('Фотография не была загружена. Попробуйте снова загрузить фотографию.')
    return ConversationHandler.END

def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation." % user.first_name)
    update.message.reply_text('Благодарим за помощь! Надеемся на дальнейшее сотрудничество.')
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=update.message.chat.id,
                    text="Сохраним природу для будущих поколений!",
                   reply_markup=reply_markup)
    return ConversationHandler.END

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [RegexHandler('^(.*?)$',
                                    custom_choice,
                                    pass_user_data=True)],
            PHOTO: [MessageHandler(Filters.photo, photo, pass_user_data=True),
                    RegexHandler('^(cancel)$', cancel),
                    CommandHandler('skip', skip_photo)],
            REPEAT: [RegexHandler('^(Да)$', start),
                     RegexHandler('^(Нет)$', cancel),
                     CommandHandler('skip', cancel)],
        },

        fallbacks=[CommandHandler('Нет', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
