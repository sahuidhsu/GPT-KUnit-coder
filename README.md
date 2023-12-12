<h1 align="center">GPT-KUnit-coder</h1>
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
    <a href="https://platform.openai.com/docs/api-reference/introduction" style="text-decoration:none" >
        <img src="https://img.shields.io/badge/OpenAI-API-00A000?style=for-the-badge&logo=openai" alt="OpenAI"/>
    </a>
</p>
<h3 align="center">a simple Python script that utilize the beta Assistant API from openAI to 
automatically create KUnit codes for Linux kernel files.</h3>
<h4 align="center">System supported: Linux, macOS(not tested) </h4>

> [!IMPORTANT]
> **This script is under development right now, so do not expect it to work properly yet.** \
> This script is only written and tested on Linux, it contains some Linux 
bash commands(E.g. ```commandA && commandB 2> error.txt```) that might not work on Windows. If you would like to use it
on Windows, feel free to modify those ```os.system()``` lines. \
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
pip3 install -r requirements.txt
```
Then, you will need to change the default configuration in [config.toml](config.toml) to your own. \
It's okay to leave `ASSISTANT_ID` and `THREAD_ID` blank, but you will need to fill in `OPENAI_API_KEY` and `LINUX_PATH`.

### Run(Auto Mode)
Using the below command to run the main script in auto mode
```bash
python3 main.py <path to file> <start line> <end line>
```
or
```bash
./main.py <path to file> <start line> <end line>
```
This will automatically generate the KUnit code for the file you specified as well as
test and self-debug. \
Please use relative path to Linux kernel root instead of absolute path. \
For example, if you want to generate KUnit code for `<linux_path>/drivers/nvme/host/trace.c` with function located 
between line 21 and 35, your command would be:
```bash
python3 main.py drivers/nvme/host/trace.c 21 35
```
There's a variable `max_debug_time` in line 357 of [main.py](main.py) that controls 
the maximum times for self-debugging. It's set to 5 by default, you can change it to any number you want.

### Run(Manual Mode)
Using the below command to run the main script by manually choosing options
```bash
python3 main.py
```
or
```bash
./main.py
```
Then you will see a menu containing some options:
#### Test generating mode
This function script will ask you for the path of the file you want to generate the KUnit code for. \
Then it will compile the file and run the tests. \
After that, if errors occurred, you can then send the errors to GPT and return back the fixed code.
#### Code fixing mode
**This function is also included in the test generating mode. If you run it individually,
you will need to enter a path to a text file that contains errors.** \
This function will send the errors to GPT and return back the fixed code.
#### Clean up mode
This function will remove the test file from Makefile, Kconfig and .kunitconfig, but not the test file itself. \
There's a double check confirmation to make sure you want to remove the test file.

### Display messages
To display all the conversation messages belongs to current thread, you can run the following command:
```bash
python3 display_messages.py
```
This script will display all the messages from the conversation with GPT. \
Please be aware that you will have to configure the threads correctly. \
This script will display the messages on the screen as well as generating a text file `message_log.txt` with the messages.

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.