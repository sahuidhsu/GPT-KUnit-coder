#!/usr/bin/env python3
###
# GPT KUnit Test Generator
# Author: LTY_CK_TS
# Copyright © 2023 by LTY_CK_TS, All Rights Reserved.
###
import os
import time

import openai
import toml

global end, config, client, assistant


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
        if time.time() - time_start > 180:
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


def initialise():
    global config, client, assistant
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


def error_fixing_mode(text=None):
    print("Entering error fixing mode...")
    if not config["THREAD_ID"]:
        print("ERROR! You should have an existing thread to send errors!")
        exit(1)
    thread_id = config["THREAD_ID"]
    thread = client.beta.threads.retrieve(thread_id=thread_id)
    if text is None:
        error_file = input("Please enter the path of the file containing the errors: ")
        error_file = os.path.abspath(error_file)
        print("Full file path: " + error_file)
        if not os.path.exists(error_file) or not os.path.isfile(error_file):
            print("ERROR! File not found!")
            exit(1)
        with open(error_file) as file:
            errors = file.read()
    else:
        errors = text
    received_content = send_message(client, thread, assistant, errors)
    if not received_content:
        exit(1)
    result_code = ""
    print("---------Generated Code-------------")
    for this_content in received_content:
        result_code = this_content[4:-4].strip()
        print(result_code)
        print("-------------------------------------")
    return result_code


def test_generating_mode():
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
                exit(1)
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
        exit(1)
    linux_path = os.path.abspath(config["LINUX_PATH"])
    if not os.path.exists(linux_path) or not os.path.isdir(linux_path):
        print("ERROR! LINUX_PATH not found or not a directory!")
        exit(1)
    filename = input("Please enter the path of the file you want to test(relative path from root of Linux kernel): ")
    file_path = linux_path + "/" + filename
    print("Full file path: " + file_path)
    if not os.path.exists(file_path):
        print("ERROR! File not found!")
        exit(1)
    with open(file_path) as file:
        code = file.readlines()
    start_line = int(input("Please enter the start line of the code: "))
    end_line = int(input("Please enter the end line of the code: "))
    print("-------------------------------------")
    code = "".join(code[start_line - 1:end_line])
    received_content = send_message(client, thread, assistant, code)
    if not received_content:
        exit(1)
    code_found = False
    return_code = ""
    print("---------Generated Code-------------")
    for this_content in received_content:
        if this_content[:4] == "```c" and this_content[-3:] == "```":
            return_code = this_content[4:-4].strip()
            code_found = True
        else:
            start_pos = this_content.find("```c")
            end_pos = this_content.rfind("```")
            if start_pos == -1 or end_pos == -1:
                print(this_content)
                print("-------------------------------------")
                print("ERROR! No code found in this response!")
                print("-------------------------------------")
                continue
            else:
                return_code = (this_content[start_pos + 4:end_pos]
                               .strip().replace("<linux/kunit/test.h>", "<kunit/test.h>"))
                code_found = True
        print(return_code)
        print("-------------------------------------")
    if not code_found:
        print("ERROR! No code found in the responses!")
        exit()
    print("Writing code to file...")
    print("-------------------------------------")
    test_file = linux_path + "/drivers/misc/tmp_kunit_test.c"
    with open(test_file, "w") as file:
        file.write(return_code)
    with open(linux_path + "/drivers/misc/Makefile") as file:
        makefile = file.readlines()
    if "obj-$(CONFIG_TMP_KUNIT_TEST) += tmp_kunit_test.o" in makefile:
        print("Test file already exists in Makefile!")
    else:
        print("Adding test file to Makefile...")
        makefile.append("\nobj-$(CONFIG_TMP_KUNIT_TEST) += tmp_kunit_test.o\n")
        with open(linux_path + "/drivers/misc/Makefile", "w") as file:
            file.writelines(makefile)
    with open(linux_path + "/drivers/misc/Kconfig") as file:
        kconfig = file.readlines()
    if "config TMP_KUNIT_TEST\n" in kconfig:
        print("TMP_KUNIT_TEST already exists in Kconfig!")
    else:
        print("Adding TMP_KUNIT_TEST to Kconfig...")
        kconfig.append("\nconfig TMP_KUNIT_TEST\n")
        kconfig.append("\ttristate \"tmp_kunit_test\" if !KUNIT_ALL_TESTS\n")
        kconfig.append("\tdepends on KUNIT\n")
        kconfig.append("\tdefault KUNIT_ALL_TESTS\n")
        with open(linux_path + "/drivers/misc/Kconfig", "w") as file:
            file.writelines(kconfig)
    with open(linux_path + "/.kunit/.kunitconfig") as file:
        kunitconfig = file.readlines()
    if "CONFIG_TMP_KUNIT_TEST=y\n" in kunitconfig:
        print("CONFIG_TMP_KUNIT_TEST already exists in .kunitconfig!")
    else:
        print("Adding CONFIG_TMP_KUNIT_TEST to .kunitconfig...")
        kunitconfig.append("\nCONFIG_TMP_KUNIT_TEST=y\n")
        with open(linux_path + "/.kunit/.kunitconfig", "w") as file:
            file.writelines(kunitconfig)
    print("-------------------------------------")
    print("Now compiling and running tests...")
    print("-------------------------------------")
    os.system("cd " + linux_path + " && ./tools/testing/kunit/kunit.py run 2> " + os.getcwd() + "/error.txt")
    with open("error.txt") as file:
        result = file.read()
    start_pos = result.find("ERROR")
    if start_pos != -1 and result.find("unsatisfied dependencies") != -1:
        print("-------------------------------------")
        print("ERROR! Unsatisfied dependencies! Please check dependencies yourself!")
        print("The test file is located at: " + test_file)
        print("-------------------------------------")
        exit(1)
    while start_pos != -1:
        print("-------------------------------------")
        print(result[start_pos:])
        print("-------------------------------------")
        print("There's error, do you want to send errors to assistant? (Y/n) ")
        entry = input()
        print("-------------------------------------")
        if entry.lower() not in ["n", "no", "dont", "not"]:
            error = result[start_pos:]
            result_code = error_fixing_mode(text=error)
            if result_code != "":
                print("Now running fixed code...")
                print("-------------------------------------")
                with open(test_file, "w") as file:
                    file.write(result_code)
                os.system("cd " + linux_path + " && ./tools/testing/kunit/kunit.py run 2> " + os.getcwd() + "/error.txt")
                with open("error.txt") as file:
                    result = file.read()
                start_pos = result.find("ERROR")
            else:
                exit(1)
        else:
            break
    print("-------------------------------------")
    print("All tests passed! Congratulations!")
    print("The test file is located at: " + test_file)
    print("-------------------------------------")


if __name__ == "__main__":
    print("-------------------------------------")
    print("GPT KUnit Test Generator")
    print("Author: LTY_CK_TS")
    print("Version: 0.1.0")
    print("-------------------------------------")
    initialise()
    end = False
    while not end:
        print("Please select mode(error fixing is also included in test generating mode):")
        print("1. Test generating mode")
        print("2. Error fixing mode")
        print("0. Exit")
        mode = input("Please enter mode: ")
        if mode == "1":
            print("-------------------------------------")
            test_generating_mode()
            end = True
        elif mode == "2":
            print("-------------------------------------")
            error_fixing_mode()
            end = True
        elif mode == "0":
            end = True
        else:
            print("-------------------------------------")
            print("ERROR! Invalid mode!")
            print("-------------------------------------")
    print("Exiting...")
