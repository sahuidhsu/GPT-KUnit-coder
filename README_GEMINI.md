<h1 align="center">GPT-KUnit-coder (Gemini Ver)</h1>
<p align="center">
    <a href="https://github.com/sahuidhsu/GPT-KUnit-coder/stargazers" style="text-decoration:none" >
        <img src="https://img.shields.io/github/stars/sahuidhsu/GPT-KUnit-coder.svg" alt="GitHub stars"/>
    </a>
    <a href="https://github.com/sahuidhsu/GPT-KUnit-coder/blob/main/LICENSE" style="text-decoration:none" >
        <img src="https://img.shields.io/github/license/sahuidhsu/GPT-KUnit-coder" alt="GitHub license"/>
    </a>
    <img src="https://img.shields.io/github/repo-size/sahuidhsu/GPT-KUnit-coder" alt="GitHub repo size"/>
    <img src="https://img.shields.io/github/last-commit/sahuidhsu/GPT-KUnit-coder" alt="GitHub last commit"/>
    <br>
    <a href="https://ai.google.dev/" style="text-decoration:none" >
        <img src="https://img.shields.io/badge/GEMINI-api-00A000?style=for-the-badge&logo=google" alt="OpenAI"/>
    </a>
</p>
<h3 align="center">This branch utilize the Gemini API via Vertex AI from Google to 
automatically create KUnit codes for Linux kernel files.</h3>
<h4 align="center">System supported: Linux, macOS(not tested) </h4>

> [!IMPORTANT]
> **This script is under development right now, it is working but may contain bugs, issues and PRs welcomed.**
> 
> This script is only written and tested on Linux, it contains some Linux 
bash commands(E.g. ```commandA && commandB 2> error.txt```) that might not work on Windows. If you would like to use it
on Windows, feel free to modify those ```os.system()``` lines.
> 
> Up to now(07/02/2024) ***Google Vertex AI*** is in a beta version, it might be unstable and not work properly.
> 
> The API is not free, you will need to have a Google Cloud account and have access to the API.

## How to use
### Requirements
- Python 3.6 or higher
- Pip installed
- Google Cloud CLI installed
- Google Cloud account with access to the Vertex AI API
### Installation
First, install dependencies:
```bash
pip3 install -r requirements.txt
```
Then, change the default configuration in [config.toml](config.toml) to your own. `LINUX_PATH` is necessary. \
Finally, install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install?hl=zh-cn) and login to your account by running the following command:
```bash
gcloud init
gcloud auth application-default login
```

### Run(Auto Mode)
Use the below command to run the main script in auto mode
```bash
python3 main.py <path to file> <start line> <end line>
```
or
```bash
./main.py <path to file> <start line> <end line>
```
This will automatically generate the KUnit code for the file you,
test it and self-debug. \
Please use relative path to Linux kernel root instead of absolute path. \
For example, if you want to generate KUnit code for `<linux_path>/drivers/nvme/host/trace.c` with function located 
between line 21 and 35, your command would be:
```bash
python3 main.py drivers/nvme/host/trace.c 21 35
```
There's a variable `max_debug_time` in line 242 of [main.py](main.py) that controls 
the maximum times for self-debugging. It's set to 5 by default, you can change it to any number you want.

### Conversation Log
The conversation log between the script and the API will be saved in `message_log.txt` if it didn't quit unexpectedly.

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
