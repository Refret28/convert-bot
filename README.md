<p align="center">
  Convert Bot
</p>

<p align="center">
  <img src="https://github.com/Refret28/convert-bot/blob/main/images/convert-bot.jpg" alt="convert-bot logo" width="300" height="300">
</p>

**You can start by clicking on the link:** [Launch bot](https://t.me/SoundHuntBot)

# Brief instructions

1) **To get started, you will need to install all the necessary libraries by running the command:**
```bash
    pip install -r requirements.txt
```

2) **Next, you need to enter the api token issued by BotFather into the configuration file (config.ini).**

3) **The last step is to change the regular expressions in the cipher.py file. You need to open this file located in pytube folder, find this code snippet:**
```python
    r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&.*?\|\|\s*([a-z]+)',
    r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',

```
**and replace them with the following:**
```python
    r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&.*?\|\|\s*([a-z]+)',
    r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])\([a-z]\)',
```
**This change will avoid errors with pytube, however the video loading speed may be reduced**