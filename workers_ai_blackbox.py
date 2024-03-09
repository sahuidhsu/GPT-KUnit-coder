#!/usr/bin/env python3
###
# GPT KUnit Test Generator Workers AI Version
# Author: LTY_CK_TS
# Copyright © 2024 by LTY_CK_TS, All Rights Reserved.
###
import os
import sys
import requests
import json

import toml

global end, config, linux_path, history

# model = "@cf/meta/llama-2-7b-chat-int8"  # llama-2-7b-chat-int8 model from Meta
# model = "@hf/thebloke/codellama-7b-instruct-awq"  # codellama-7b-instruct-awq model from Meta via Hugging Face
model = "@hf/thebloke/deepseek-coder-6.7b-instruct-awq"  # deepseek-coder with instruct-awq model from Hugging Face


def send_message(history, msg):
    print("Message sent! Now waiting for reply...")
    history.append({"role": "user", "content": msg})
    response_text = ""
    response = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        json={"stream": True, "messages": history},
        stream=True,
    )
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line == 'data: [DONE]':
                print("\nMessage received!")
                break
            else:
                try:
                    json_line = json.loads(decoded_line.split(': ')[1])
                    response_text += json_line["response"]
                    print(json_line["response"], end="")
                except BaseException:
                    print(decoded_line)
                    history.append({"role": "system", "content": decoded_line})
                    write_log()
                    print("ERROR! JSON decode error!")
                    exit(1)
    history.append({"role": "system", "content": response_text})
    return response_text


def write_log():
    log = open("message_log.txt", "w")
    for message in history:
        log.write(f"{message['role']}\n{'-' * 20}\n {message['content']}\n{'-' * 20}\n")
    log.close()


def initialise():
    global config, linux_path, account_id, api_token, history
    with open("config.toml") as config_file:
        config = toml.load(config_file)

    if not config["LINUX_PATH"]:
        print("ERROR! Please set your LINUX_PATH in config.toml")
        exit(1)
    linux_path = os.path.abspath(config["LINUX_PATH"])
    if not os.path.exists(linux_path) or not os.path.isdir(linux_path):
        print("ERROR! LINUX_PATH not found or not a directory!")
        exit(1)
    if not config["CF_API_KEY"]:
        print("ERROR! Please set your CF_API_KEY in config.toml")
        exit(1)
    if not config["CF_ACCOUNT_ID"]:
        print("ERROR! Please set your CF_ACCOUNT_ID in config.toml")
        exit(1)
    account_id = config["CF_ACCOUNT_ID"]
    api_token = config["CF_API_KEY"]
    template = ("#include <kunit/test.h>\nstatic void test(struct kunit *test)\n{KUNIT_EXPECT_EQ(test, 1, 1);}\n"
                "static struct kunit_case test_cases[] = {\nKUNIT_CASE(test),\n{}\n"
                "static struct kunit_suite test_suite = {\n.name = \"test_cases\",\n.test_cases = test_cases,\n};\n"
                "kunit_test_suite(test_suite);\nMODULE_LICENSE(\"GPL\");")
    history = [{"role": "system", "content": "The lib of KUnit is <kunit/test.h>.\nBelow is a "
                                             f"template of KUnit test file:\n```c\n{template}\n```"
                }]
    print("-------------------------------------")


def error_fixing_mode(text=None):
    print("Entering error fixing mode...")
    errors = (f"Below is the result of running:\n```\n{text[:2000]}\n```\nPlease fix the errors and return only "
              f"the fixed code. "
              f"Make sure your code is inside ```c and ```.")
    this_content = send_message(history, errors)
    if not this_content:
        write_log()
        print("ERROR! No response received!")
        return ""
    if this_content[:4] == "```c" and this_content[-3:] == "```":
        result_code = this_content[4:-4].strip()
    else:
        start_pos = this_content.find("```c")
        end_pos = this_content.rfind("```")
        if start_pos == -1 or end_pos == -1:
            print(this_content)
            print("-------------------------------------")
            print("ERROR! No code found in this response!")
            print("-------------------------------------")
            write_log()
            return ""
        else:
            result_code = (this_content[start_pos + 4:end_pos].strip())
        print("-------------------------------------")
    return result_code


def test_generating_mode(func=None, help=None):
    print("Entering test generating mode...")
    if not func:
        print("ERROR! No function name provided!")
        exit(1)
    print("-------------------------------------")
    prompt = "I want you to generate a KUnit test file for the function ```" + func + "``` in Linux kernel."
    if help:
        prompt += f"\n{help}"
    this_content = send_message(history, prompt)
    if not this_content:
        write_log()
        exit(1)
    print("---------Generated Code-------------")
    if this_content[:4] == "```c" and this_content[-3:] == "```":
        return_code = this_content[4:-4].strip()
    else:
        start_pos = this_content.find("```c")
        end_pos = this_content.rfind("```")
        if start_pos == -1 or end_pos == -1:
            print(this_content)
            print("-------------------------------------")
            print("ERROR! No code found in this response!")
            print("-------------------------------------")
            write_log()
            exit(1)
        else:
            return_code = (this_content[start_pos + 4:end_pos]
                           .strip().replace("<linux/kunit.h>", "<kunit/test.h>"))
        print("-------------------------------------")
    print("Writing code to file...")
    print("-------------------------------------")

    test_file = linux_path + "/drivers/misc/tmp_kunit_test.c"
    with open(test_file, "w") as file:
        file.write(return_code)

    with open(linux_path + "/drivers/misc/Makefile") as file:
        makefile = file.readlines()

    if "obj-$(CONFIG_TMP_KUNIT_TEST) += tmp_kunit_test.o\n" in makefile:
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
    os.system(f"echo '' > {os.getcwd()}/error.txt")
    os.system(f"cd {linux_path} && ./tools/testing/kunit/kunit.py run > {os.getcwd()}/error.txt 2>&1")

    # Self-debugging
    with open("error.txt") as file:
        result = file.read()

    error_pos = result.find("ERROR")
    fail_pos = result.find("[FAILED]")
    start_pos = error_pos if error_pos != -1 else fail_pos
    if start_pos != -1 and result.find("unsatisfied dependencies") != -1:
        print("-------------------------------------")
        print("ERROR! Unsatisfied dependencies! Please check dependencies yourself!")
        print("The test file is located at: " + test_file)
        print("-------------------------------------")
        exit(1)

    debug_times = 0
    while start_pos != -1:
        if debug_times >= max_debug_time:
            write_log()
            print("-------------------------------------")
            print("Max self-debugging times exceeded! Exiting...")
            print("The uncompleted test file is located at: " + test_file)
            print("-------------------------------------")
            exit(0)
        print("-------------------------------------")
        print(result)
        print("-------------------------------------")
        error = result
        debug_times += 1
        print(f"Self-debugging times: {debug_times}")
        result_code = error_fixing_mode(text=error).replace("`", "")
        if result_code != "":
            print("Now running fixed code...")
            print("-------------------------------------")
            with open(test_file, "w") as file:
                file.write(result_code)

            os.system(f"echo '' > {os.getcwd()}/error.txt")
            os.system(f"cd {linux_path} && ./tools/testing/kunit/kunit.py run > {os.getcwd()}/error.txt 2>&1")

            with open("error.txt") as file:
                result = file.read()

            error_pos = result.find("ERROR")
            fail_pos = result.find("[FAILED]")
            start_pos = error_pos if error_pos != -1 else fail_pos
        else:
            exit(1)
    write_log()
    print("-------------------------------------")
    print("All tests passed! Congratulations!")
    print("The test file is located at: " + test_file)
    print("-------------------------------------")


if __name__ == "__main__":
    print("-------------------------------------")
    print("GPT KUnit Test Generator Workers AI Ver")
    if len(sys.argv) > 1:
        initialise()
        try:
            func_name = sys.argv[1]
            help_text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        except ValueError:
            print("ERROR! Invalid input!")
            exit(1)
        max_debug_time = 5
        print(f"Auto mode enabled, max self-debugging times: {max_debug_time}")
        print("Author: LTY_CK_TS")
        print("Version: 0.1.0")
        print("-------------------------------------")
        test_generating_mode(func=func_name, help=help_text)
    print("Exiting...")
