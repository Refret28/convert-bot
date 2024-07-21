import os
import logging
import telebot
from telebot import types
from conversion import download_and_convert_video, download_thumbnail

user_choices = {}
user_states = {}
WAITING_NEXT_COMMAND = 'waiting_next_command'
CHOOSING_OPTION = 'choosing_option'
AWAITING_QUERY = 'awaiting_query'

def register_handlers(bot: telebot.TeleBot):
    @bot.message_handler(commands=['start'])
    def cmd_start(message: telebot.types.Message):
        user_states[message.from_user.id] = AWAITING_QUERY
        bot.send_message(message.chat.id, 'Welcome! Enter the video title to search for it on YouTube. Please write the full title for a relevant search.')

    @bot.message_handler(commands=['stop'])
    def cmd_stop(message: telebot.types.Message):
        user_states[message.from_user.id] = None
        bot.send_message(message.chat.id, 'Stopped. To resume, enter the command /start.')

    @bot.message_handler(commands=['next'])
    def cmd_next(message: telebot.types.Message):
        user_states[message.from_user.id] = AWAITING_QUERY
        bot.send_message(message.chat.id, 'Enter the title of the next video:')

    @bot.message_handler(content_types=['text'])
    def process_text_messages(message: telebot.types.Message):
        user_id = message.from_user.id
        if user_states.get(user_id) == WAITING_NEXT_COMMAND:
            if message.text == '/next':
                user_states[user_id] = AWAITING_QUERY
                bot.send_message(message.chat.id, 'Enter the title of the next video:')
            else:
                bot.send_message(message.chat.id, 'Command not found. Enter the command /next to continue.')
        elif user_states.get(user_id) == AWAITING_QUERY:
            try:
                user_choices[message.from_user.id] = {'query': message.text}
                user_states[user_id] = CHOOSING_OPTION

                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add(types.KeyboardButton('🎼Audio only'))
                markup.add(types.KeyboardButton('🎼🔗Audio + video link'))

                message_to_send = 'Choose an option:'
                bot.send_message(message.chat.id, message_to_send, reply_markup=markup)

            except ValueError as ve:
                logging.warning(f'Error processing request: {ve}')
                bot.send_message(message.chat.id, f'Error processing request')
                bot.send_message(message.chat.id, 'To continue, enter the command: /next')
                user_states[user_id] = WAITING_NEXT_COMMAND
            except Exception as e:
                logging.exception(f'Unhandled error processing request: {e}')
                bot.send_message(message.chat.id, 'An error occurred processing the request. Please try again.')
                bot.send_message(message.chat.id, 'To continue, enter the command: /next')
                user_states[user_id] = WAITING_NEXT_COMMAND
        elif user_states.get(user_id) == CHOOSING_OPTION:
            process_choice(bot, message)
        else:
            bot.send_message(message.chat.id, 'To start, enter the command /start.')

def remove_path(path) -> None:
    if path is None:
        return
    elif os.path.exists(path):
        os.remove(path) 

def process_choice(bot, message: telebot.types.Message):
    file_path = None
    thumbnail_path = None
    
    try:
        user_id = message.from_user.id
        choice = message.text
        
        if choice not in ['🎼Audio only', '🎼🔗Audio + video link']:
            bot.send_message(message.chat.id, 'Invalid choice. Please select an option from the given choices.')
            return

        query = user_choices[user_id]['query']
        bot.send_message(message.chat.id, 'Please wait...', reply_markup=types.ReplyKeyboardRemove())
        file_path, video_url, thumbnail_url, title = download_and_convert_video(query, choice == '🎼🔗Audio + video link')
        
        with open(file_path, 'rb') as audio_file:
            bot.send_message(message.chat.id, 'Sending audio...')
    
            thumbnail_path = download_thumbnail(thumbnail_url) if thumbnail_url else None
            
            if 'user_choice' not in user_choices[user_id]:
                user_choices[user_id]['user_choice'] = choice
            elif user_choices[user_id]['user_choice'] == '🎼Audio only' and choice == '🎼🔗Audio + video link':
                user_choices[user_id]['user_choice'] = choice

            video_caption = f'Video link: {video_url}' if video_url else None
    
            if user_choices[user_id]['user_choice'] == '🎼🔗Audio + video link':
                bot.send_audio(
                    chat_id=user_id,
                    audio=audio_file,
                    title=title,
                    caption=video_caption,
                    thumb=open(thumbnail_path, 'rb') if thumbnail_path else None
                )
            else:
                bot.send_audio(
                    chat_id=user_id,
                    audio=audio_file,
                    title=title,
                    thumb=open(thumbnail_path, 'rb') if thumbnail_path else None
                )
    
            bot.send_message(message.chat.id, 'To continue, enter the command: /next')
            user_states[user_id] = WAITING_NEXT_COMMAND
    
    except ValueError as ve:
        logging.warning(f'Error processing request: {ve}')
        bot.send_message(message.chat.id, f'Error downloading video')
        bot.send_message(message.chat.id, 'To continue, enter the command: /next')
        user_states[user_id] = WAITING_NEXT_COMMAND
    
    except Exception as e:
        logging.exception(f'Unhandled error processing request: {e}')
        bot.send_message(message.chat.id, 'An error occurred processing the request. Please try again.')
        bot.send_message(message.chat.id, 'To continue, enter the command: /next')
        user_states[user_id] = WAITING_NEXT_COMMAND
    
    finally:
        remove_path(file_path)
        remove_path(thumbnail_path)
