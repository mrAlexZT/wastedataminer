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

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

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
    reply_keyboard.append(['я не знаю что это'])
    reply_keyboard.append(['cancel'])
    return reply_keyboard

reply_keyboard = make_keyboard(2)

def start(bot, update):
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=update.message.chat.id,
                    text="Загрузите изображение!",
                   reply_markup=reply_markup)
    return PHOTO

def custom_choice(bot, update, user_data):
    text = update.message.text
    user_data['choice'] = text
    os.rename(user_data['filename'], user_data['filename'].replace("--","-"+user_data['choice']+"-"))
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
    fn = "files/{}-{}-{}-{}.jpg".format(user.id,text,time.time(),'001')
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
