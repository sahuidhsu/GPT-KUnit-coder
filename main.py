import openai
import os
import toml

with open("config.toml") as config_file:
    config = toml.load(config_file)

if not config["OPENAI_API_KEY"]:
    print("ERROR! Please set your OPENAI_API_KEY in config.toml")
    exit()

openai.api_key = config["OPENAI_API_KEY"]
if not config["ASSISTANT_ID"]:
    assistant = openai.beta.assistants.create(name="KUnit developer",
                                              instructions="You are a developer who is very familiar with the KUnit "
                                                           "tests in Linux kernel.\nUser will send you pieces of "
                                                           "source code. You should create some executable "
                                                           "corresponding KUnit test cases to test out the code."
                                                           "\nDo not include any sentences other than the code "
                                                           "itself in your reply.",
                                              tools=[],
                                              model="gpt-4-1106-preview")
    with open("config.toml", "w") as config_file:
        config["ASSISTANT_ID"] = assistant.id
        toml.dump(config, config_file)
else:
    assistant_id = config["ASSISTANT_ID"]
    assistant = openai.beta.assistants.retrieve(assistant_id=assistant_id)

if not config["THREAD_ID"]:
    thread = openai.beta.threads.create()
    with open("config.toml", "w") as config_file:
        config["THREAD_ID"] = thread.id
        toml.dump(config, config_file)
else:
    thread_id = config["THREAD_ID"]
    thread = openai.beta.threads.retrieve(thread_id=thread_id)

if not config["LINUX_PATH"]:
    print("ERROR! Please set your LINUX_PATH in config.toml")
    exit()
linux_path = os.path.abspath(config["LINUX_PATH"])
if not os.path.exists(linux_path) or not os.path.isdir(linux_path):
    print("ERROR! LINUX_PATH not found or not a directory!")
    exit()
file_path = input("Please enter the path of the file you want to test(relative path from root of Linux kernel): ")
file_path = linux_path + file_path
if not os.path.exists(file_path):
    print("ERROR! File not found!")
    exit()
with open(file_path) as file:
    code = file.read()

