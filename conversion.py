import os
import requests
from youtubesearchpython import VideosSearch
from pytube import YouTube

def download_and_convert_video(query: str, send_video_link: bool = False):
    file_path = None
    try:
        videos_search = VideosSearch(query, limit=1)
        results = videos_search.result()

        if results['result']:
            video_url = results['result'][0]['link']
            yt = YouTube(video_url)
            thumbnail_url = yt.thumbnail_url

            audio_stream = yt.streams.filter(only_audio=True).first()

            if audio_stream:
                file_path = audio_stream.download()
                if os.path.getsize(file_path) > 20 * 1024 * 1024: 
                    os.remove(file_path)
                    raise ValueError('The file size exceeds the limit of 20 MB')
                return file_path, video_url, thumbnail_url if send_video_link else None, yt.title
            else:
                raise ValueError('Failed to find audio stream')
        else:
            raise ValueError('Video not found')
    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise ValueError(f'Error downloading video: {e}')
    
def download_thumbnail(thumbnail_url: str) -> str:
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        file_path = 'thumbnail.png'
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return file_path
    else:
        raise ValueError('Failed to download thumbnail')
