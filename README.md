# GPT-KUnit-coder
[![OpenAI](https://img.shields.io/badge/OpenAI-API-08FF00?style=for-the-badge&logo=openai)](https://beta.openai.com/docs/api-reference/introduction)
## Introduction
This is a simple Python script that utilize the beta Assistant API from openAI to automatically
create KUnit codes for Linux kernel files.
> [!IMPORTANT]
> Currently(23/11/2023) ***Assistant API*** is in a beta version, so it can be unstable and not work properly.
> Also, the API is not free, you will need to have an OpenAI account and have access to the API.

## How to use
### Installation
First, you will need to install dependencies:
```bash
pip install -r requirements.txt
```
Then, you will need to change the default configuration in [config.toml](config.toml) to your own.

### Run
To run the script, you will need to run the following command:
```bash
python main.py
```
The script will ask you for the path of the file you want to generate the KUnit code for.

...