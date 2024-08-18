# YouTube Audio Downloading Telegram Bot

This bot allows users to search for YouTube videos and download audio, with the option to include a link to the original video. The bot uses the Aiogram framework and the yt_dlp library for extracting video information. FFmpeg is required for audio processing. Follow the instructions below for installation and setup.

**Features**

<li><strong>Start Command (/start):</strong> Initializes the bot and prompts the user to enter a video title to search on YouTube.</li>
<li><strong>Stop Command (/stop):</strong> Stops the bot's interaction with the user.</li>
<li><strong>Next Command (/next):</strong> Allows the user to search for another video.</li>
<li><strong>Video Search & Audio Download:</strong> Users can search for a video by entering its full title. The bot provides options to download only the audio or the audio with a link to the video.</li>
<li><strong>Error Handling:</strong> The bot handles common errors, such as network issues and file size limitations, providing relevant feedback to the user.</li>
<li><strong>Session Management:</strong> The bot tracks user states to manage ongoing interactions and prevent duplicate entries.</li>

## Installation and Setup

1) **Clone the Repository:**
```bash
  git clone https://github.com/Refret28/convert-bot.git
```
```bash
  cd convert-bot
```

2) **Install Dependencies:**
```bash
  pip install -r requirements.txt
```
The requirements.txt file includes all necessary dependencies, including the yt_dlp library, which is used for extracting video information from YouTube. yt_dlp is a fork of youtube-dl with updated features for working with YouTube.

3) **Install FFmpeg:**

The bot uses FFmpeg for processing audio files. Install FFmpeg as follows:

<li><strong>For Windows:</strong></li><br>

Download FFmpeg from the official website: https://ffmpeg.org/download.html.
Extract the archive and add the FFmpeg path to your system's PATH environment variable.

<li><strong>For macOS:</strong></li><br>

Install FFmpeg via Homebrew:
```bash
  brew install ffmpeg 
```
<li><strong>For Linux:</strong></li><br>

Install FFmpeg using your system's package manager. For example, on Ubuntu:
```bash
  sudo apt update
```
```bash
  sudo apt install ffmpeg
```
4) **Configuration:**
Insert your Telegram Bot API token, path to bin and path to dir to remove residual files after downloading into the config.ini file under the [BOT TOKEN], [PATH TO BIN] and [PATH TO DIR] sections.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your improvements.
