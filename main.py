###
# GPT KUnit Test Generator
# Author: LTY_CK_TS
# Copyright © 2023 by LTY_CK_TS, All Rights Reserved.
###
import os
import sys
import time

import openai
import toml


def send_message(msg_client, msg_thread, msg_assistant, msg):
    message = msg_client.beta.threads.messages.create(
        thread_id=msg_thread.id,
        role="user",
        content=msg
    )
    run = msg_client.beta.threads.runs.create(
        thread_id=msg_thread.id,
        assistant_id=msg_assistant.id,
    )
    print("Message sent! Now waiting for reply...")
    time.sleep(1)
    run_ret = msg_client.beta.threads.runs.retrieve(
        thread_id=msg_thread.id,
        run_id=run.id
    )
    time_start = time.time()
    while run_ret.status != "completed":
        run_ret = msg_client.beta.threads.runs.retrieve(
            thread_id=msg_thread.id,
            run_id=run.id
        )
        time.sleep(3)
        if time.time() - time_start > 60:
            print("ERROR! Timeout waiting for responses!")
            return None
    print("Message received!")
    messages = msg_client.beta.threads.messages.list(
        thread_id=msg_thread.id,
        before=message.id
    )
    contents = []
    for this_msg in messages.data:
        if this_msg.role == "assistant":
            contents.append(this_msg.content[0].text.value)
    contents.reverse()
    return contents


with open("config.toml") as config_file:
    config = toml.load(config_file)

if not config["OPENAI_API_KEY"]:
    print("ERROR! Please set your OPENAI_API_KEY in config.toml")
    exit()

client = openai.Client(api_key=config["OPENAI_API_KEY"])

if not config["ASSISTANT_ID"]:
    print("No existing assistant found. Now creating new assistant...")
    assistant = client.beta.assistants.create(name="KUnit developer",
                                              instructions="You are a developer who is very familiar with the KUnit "
                                                           "tests in Linux kernel.\nUser will send you pieces of "
                                                           "source code. You should create some executable "
                                                           "corresponding KUnit test cases to test out the code."
                                                           "User may also send you errors that occur when running,"
                                                           "you should fix the errors and send back the fixed code."
                                                           "\nDo not include any sentences other than the code "
                                                           "itself in your reply. You should implement all the codes,"
                                                           "do not leave any space for the user to add any code.",
                                              tools=[],
                                              model="gpt-4-1106-preview")
    with open("config.toml", "w") as config_file:
        config["ASSISTANT_ID"] = assistant.id
        toml.dump(config, config_file)
else:
    assistant_id = config["ASSISTANT_ID"]
    assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)

if len(sys.argv) > 1:
    print("Entering error fixing mode...")
    if not config["THREAD_ID"]:
        print("ERROR! You should have an existing thread to send errors!")
        exit()
    thread_id = config["THREAD_ID"]
    thread = client.beta.threads.retrieve(thread_id=thread_id)
    error_file = os.path.abspath(sys.argv[1])
    if not os.path.exists(error_file) or not os.path.isfile(error_file):
        print("ERROR! File not found!")
        exit()
    with open(error_file) as file:
        errors = file.read()
    received_content = send_message(client, thread, assistant, errors)
    print("---------Generated Code-------------")
    for this_content in received_content:
        print(this_content[4:-4].strip())
        print("-------------------------------------")
else:
    print("Entering test generating mode...")
    if not config["THREAD_ID"]:
        print("No existing thread found. Now creating new thread...")
        thread = client.beta.threads.create()
        with open("config.toml", "w") as config_file:
            config["THREAD_ID"] = thread.id
            toml.dump(config, config_file)
    else:
        entry = input("Do you want to start a new thread? (y/N) ")
        if entry in ["y", "Y"]:
            delete_thread = client.beta.threads.delete(thread_id=config["THREAD_ID"])
            if not delete_thread.deleted:
                print("ERROR! Failed to delete thread!")
                exit()
            print("Thread deleted! Now creating new thread...")
            thread = client.beta.threads.create()
            with open("config.toml", "w") as config_file:
                config["THREAD_ID"] = thread.id
                toml.dump(config, config_file)
        else:
            print("Using existing thread...")
            thread_id = config["THREAD_ID"]
            thread = client.beta.threads.retrieve(thread_id=thread_id)
    if not config["LINUX_PATH"]:
        print("ERROR! Please set your LINUX_PATH in config.toml")
        exit()
    linux_path = os.path.abspath(config["LINUX_PATH"])
    if not os.path.exists(linux_path) or not os.path.isdir(linux_path):
        print("ERROR! LINUX_PATH not found or not a directory!")
        exit()
    filename = input("Please enter the path of the file you want to test(relative path from root of Linux kernel): ")
    file_path = linux_path + "/" + filename
    print("Full file path: " + file_path)
    if not os.path.exists(file_path):
        print("ERROR! File not found!")
        exit()
    with open(file_path) as file:
        code = file.readlines()
    start_line = int(input("Please enter the start line of the code: "))
    end_line = int(input("Please enter the end line of the code: "))
    code = "".join(code[start_line - 1:end_line])
    received_content = send_message(client, thread, assistant, code)
    print("---------Generated Code-------------")
    for this_content in received_content:
        print(this_content[4:-4].strip())
        print("-------------------------------------")
    print("Now please test the code and log the errors into a file. "
          "Then run this script with the file as argument.(E.g. python3 main.py errors.txt)")
