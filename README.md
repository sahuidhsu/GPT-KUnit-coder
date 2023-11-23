# GPT-KUnit-coder
[![OpenAI](https://img.shields.io/badge/OpenAI-API-08FF00?style=for-the-badge&logo=openai)](https://beta.openai.com/docs/api-reference/introduction)
## Introduction
This is a simple Python script that utilize the beta Assistant API from openAI to automatically
create KUnit codes for Linux kernel files.
> [!IMPORTANT]
> **This script is under development right now, so do not expect it to work properly yet.** \
> Currently(23/11/2023) ***Assistant API*** is in a beta version, so it can be unstable and not work properly. \
> Also, the API is not free, you will need to have an OpenAI account and have access to the API.

## How to use
### Requirements
- Python 3.6 or higher
- Pip installed
- OpenAI account with access to the Assistant API
- A valid API key
### Installation
First, you will need to install dependencies:
```bash
pip install -r requirements.txt # if you are using Windows
pip3 install -r requirements.txt # if you are using Linux/MacOS
```
Then, you will need to change the default configuration in [config.toml](config.toml) to your own. \
It's okay to leave `ASSISTANT_ID` and `THREAD_ID` blank, but you will need to fill in `OPENAI_API_KEY` and `LINUX_PATH`.

### Run
To run the script, you will need to run the following command:
```bash
python main.py  # if you are using Windows
python3 main.py # if you are using Linux/MacOS
```
The script will ask you for the path of the file you want to generate the KUnit code for.

...