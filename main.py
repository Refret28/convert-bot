import logging
import os
import json
from pathlib import Path
import configparser
from datetime import datetime, timedelta

import asyncio
from aiohttp import ClientConnectorError

from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError

from conversion import download_and_convert_video, download_thumbnail

config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['BOT TOKEN']['TOKEN']

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

WAITING_NEXT_COMMAND = 'waiting_next_command'
CHOOSING_OPTION = 'choosing_option'
AWAITING_QUERY = 'awaiting_query'

USER_STATE_FILE = 'user_states.json'
STATUS_FILE = 'bot_status.json'
USER_CHOICES_FILE = 'user_choices.json'

BOT_WAS_DOWN = False

def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def load_json(file_path, default_data=None):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            return default_data or {}
    else:
        return default_data or {}
    
def add_user_if_not_exists(user_dict, user_id, default_value):
    if user_id not in user_dict:
        user_dict[user_id] = default_value
        return True
    return False

def save_user_states(user_states) -> None:
    save_json(USER_STATE_FILE, user_states)

def load_user_states():
    return load_json(USER_STATE_FILE, default_data={})

def save_user_choices(user_choices) -> None:
    save_json(USER_CHOICES_FILE, user_choices)

def load_user_choices():
    return load_json(USER_CHOICES_FILE, default_data={})

def clean_duplicates(user_states, user_choices):
    user_states = dict.fromkeys(user_states)
    user_choices = dict.fromkeys(user_choices)
    save_user_states(user_states)
    save_user_choices(user_choices)

def get_current_date():
    return datetime.now().isoformat()

def remove_old_users(user_choices):
    one_week_ago = datetime.now() - timedelta(weeks=1)
    user_choices = {user_id: data for user_id, data in user_choices.items()
                    if datetime.fromisoformat(data.get('date', '')) >= one_week_ago}
    return user_choices

@dp.message(Command('start'))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if add_user_if_not_exists(user_states, user_id, AWAITING_QUERY):
        save_user_states(user_states)
    user_states[user_id] = AWAITING_QUERY  
    save_user_states(user_states)
    await message.answer('Welcome! Enter the title of the video to find it on YouTube. Please provide the full title for the most relevant search.')

@dp.message(Command('stop'))
async def cmd_stop(message: Message):
    user_id = message.from_user.id
    if add_user_if_not_exists(user_states, user_id, None):
        save_user_states(user_states)
    user_states[user_id] = None  
    save_user_states(user_states)
    await message.answer('Stopped. To continue, enter the /start command.')

@dp.message(Command('next'))
async def cmd_next(message: Message):
    user_id = message.from_user.id
    if add_user_if_not_exists(user_states, user_id, AWAITING_QUERY):
        save_user_states(user_states)
    user_states[user_id] = AWAITING_QUERY
    save_user_states(user_states)
    await message.answer('Enter the title of the next video:')

@dp.message()
async def process_text_messages(message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        user_states[user_id] = WAITING_NEXT_COMMAND
        save_user_states(user_states)
        
    if user_states.get(user_id) == WAITING_NEXT_COMMAND:
        if message.text != '/next':
            await message.answer('Command not found. Enter the /next command to continue.')
    elif user_states.get(user_id) == AWAITING_QUERY:
        try:
            user_choices[user_id] = {
                'query': message.text,
                'date': get_current_date()  
            }
            save_user_choices(user_choices) 
            user_states[user_id] = CHOOSING_OPTION
            save_user_states(user_states) 

            kb = [
                [
                    types.KeyboardButton(text="🎼Audio only"),
                    types.KeyboardButton(text="🎼🔗Audio + video link")
                ],
            ]
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True,
                input_field_placeholder="Choose an option"
            )
            await message.answer('Choose an option:', reply_markup=keyboard)

        except ValueError as ve:
            logging.warning(f'Request processing error: {ve}')
            await message.answer('Request processing error')
            await message.answer('To continue, enter the /next command')
            user_states[user_id] = WAITING_NEXT_COMMAND
            save_user_states(user_states)
        except Exception as e:
            logging.exception(f'Unhandled request processing error: {e}')
            await message.answer('An error occurred while processing the request. Please try again.')
            await message.answer('To continue, enter the /next command')
            user_states[user_id] = WAITING_NEXT_COMMAND
            save_user_states(user_states)
    elif user_states.get(user_id) == CHOOSING_OPTION:
        await process_choice(message)
    else:
        await message.answer('To start, enter the /start command.')


def remove_path(path) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            logging.error(f'Error deleting file {path}: {e}')

def remove_all_files() -> None:
    path_to_dir = config['PATH TO DIR']['PATH']
    path = Path(path_to_dir)
    for file in path.glob("*"):
        if file.suffix in ['.part', '.mp3']:
            file.unlink()

async def process_choice(message: types.Message):
    file_path = None
    thumbnail_path = None

    try:
        user_id = message.from_user.id
        choice = message.text

        if choice not in ['🎼Audio only', '🎼🔗Audio + video link']:
            await message.answer('Invalid choice. Please select an option from the suggested ones.')
            return

        query = user_choices[user_id]['query']
        start_msg = await message.answer('Downloading started...', reply_markup=types.ReplyKeyboardRemove())

        file_path, video_url, thumbnail_url, title = await download_and_convert_video(query, choice == '🎼🔗Audio + video link')
        
        audio_file = FSInputFile(file_path)
        thumbnail_path = await download_thumbnail(thumbnail_url) if thumbnail_url else None

        if user_choices[user_id].get('user_choice') is None:
            user_choices[user_id]['user_choice'] = choice
        elif user_choices[user_id]['user_choice'] == '🎼Audio only' and choice == '🎼🔗Audio + video link':
            user_choices[user_id]['user_choice'] = choice

        video_caption = f'Video link: {video_url}' if video_url else None

        if user_choices[user_id]['user_choice'] == '🎼🔗Audio + video link':
            await bot.send_audio(
                chat_id=user_id,
                audio=audio_file,
                title=title,
                thumbnail=FSInputFile(thumbnail_path) if thumbnail_path else None
            )
            if thumbnail_path:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=FSInputFile(thumbnail_path),
                    caption=video_caption
                )
        else:
            await bot.send_audio(
                chat_id=user_id,
                audio=audio_file,
                title=title,
                thumbnail=FSInputFile(thumbnail_path) if thumbnail_path else None
            )

        await start_msg.delete()
        await message.answer('To continue, enter the /next command')
        user_states[user_id] = WAITING_NEXT_COMMAND
        save_user_states(user_states) 

    except ValueError as ve:
        logging.warning(f'Request processing error: {ve}')
        if 'File size > 20 MB' in str(ve):
            await message.answer('File size is greater than 20 MB. Please try a smaller video.')
        else:
            await message.answer('Error downloading video. Please try again.')
        await message.answer('To continue, enter the /next command')
        user_states[user_id] = WAITING_NEXT_COMMAND
        save_user_states(user_states) 

    except Exception as e:
        logging.exception(f'Unhandled request processing error: {e}')
        await message.answer('An error occurred while processing the request. Please try again.')
        await message.answer('To continue, enter the /next command')
        user_states[user_id] = WAITING_NEXT_COMMAND
        save_user_states(user_states) 

    finally:
        remove_path(file_path)
        remove_path(thumbnail_path)
        remove_all_files()

async def notify_users(message: str):
    user_states = load_user_states()
    for user_id in user_states.keys():
        try:
            await bot.send_message(user_id, message)
        except Exception as send_error:
            logging.error(f'Failed to send message to user {user_id}: {send_error}')

async def main():
    global BOT_WAS_DOWN
    global user_states
    global user_choices

    user_states = load_user_states()
    user_choices = load_user_choices()

    clean_duplicates(user_states, user_choices)

    user_choices = remove_old_users(user_choices)

    save_user_states(user_states)
    save_user_choices(user_choices)

    save_json(STATUS_FILE, {'online': True})
    
    status = load_json(STATUS_FILE, default_data={'online': True})
    BOT_WAS_DOWN = not status.get('online', True)
    
    try:
        await dp.start_polling(bot)
        if BOT_WAS_DOWN:
            await notify_users('The bot is back online. We apologize for the temporary inconvenience.')
            BOT_WAS_DOWN = False
            save_json(STATUS_FILE, {'online': True})
    except (TelegramAPIError, ClientConnectorError) as e:
        logging.error(f'Error running bot: {e}')
        await bot.answer('Network error. Please try again.')
        BOT_WAS_DOWN = True
        save_json(STATUS_FILE, {'online': False})
    except Exception as e:
        logging.error(f'Unhandled error: {e}')
        await bot.answer('Unexpected error. Please try again.')
        BOT_WAS_DOWN = True
        save_json(STATUS_FILE, {'online': False})
    finally:
        if BOT_WAS_DOWN:
            await notify_users('The bot is temporarily down due to a connection issue. Please try again later.')
        save_json(STATUS_FILE, {'online': False})
        save_user_states(user_states)
        save_user_choices(user_choices)

if __name__ == "__main__":
    asyncio.run(main())
