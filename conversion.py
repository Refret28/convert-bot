import asyncio
import aiohttp
import aiofiles

from yt_dlp import YoutubeDL

import configparser
from pathlib import Path

config = configparser.ConfigParser()
config.read('config.ini')
PATH_TO_BIN = config['PATH TO BIN']['PATH']

ydl_opts = {
    'format': 'bestaudio[ext=mp4]/bestaudio/best',
    'external_downloader': 'aria2c',
    'external_downloader_args': ['-x', '16', '-k', '1M'],
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',
    }],
    'outtmpl': '%(title)s.%(ext)s',
    'noplaylist': True,
    'retries': 10,
    'socket_timeout': 30,
    'http_chunk_size': 10485760,
    'ffmpeg_location': PATH_TO_BIN,
    'max_filesize': 20 * 1024 * 1024,
    'throttled-rate': None,
    'concurrent_fragment_downloads': 4
}

async def download_and_convert_video(query: str, send_video_link: bool = False):
    try:
        ydl = YoutubeDL(ydl_opts)
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch:{query}", download=True))

        if 'entries' in info:
            video_info = info['entries'][0]
            video_url = video_info['webpage_url']
            temp_file_path = Path(ydl.prepare_filename(video_info)).with_suffix('.part')
            final_file_path = temp_file_path.with_suffix('.mp3')

            if temp_file_path.exists():
                temp_file_path.rename(final_file_path)

            if final_file_path.stat().st_size > 20 * 1024 * 1024:
                final_file_path.unlink()
                raise ValueError('File size > 20 MB')

            thumbnail_url = video_info['thumbnail'] if send_video_link else None
            return final_file_path, video_url, thumbnail_url, video_info['title']

        raise ValueError('Video not found')

    except Exception as e:
        if 'final_file_path' in locals() and final_file_path.exists():
            final_file_path.unlink()
        raise ValueError(f'Error downloading video: {e}')

async def download_thumbnail(thumbnail_url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail_url) as response:
            if response.status == 200:
                file_path = Path('thumbnail.png')
                async with aiofiles.open(file_path, 'wb') as file:
                    await file.write(await response.read())
                return str(file_path)
            else:
                raise ValueError('Error downloading thumbnail')
