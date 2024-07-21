import logging
import telebot
from handler import register_handlers
import configparser

config = configparser.ConfigParser()
config.read('config1.ini')
TOKEN = config['DEFAULT']['TOKEN']

bot = telebot.TeleBot(TOKEN)

register_handlers(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bot.polling(none_stop=True)
