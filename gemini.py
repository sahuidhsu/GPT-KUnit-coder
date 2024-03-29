#!/usr/bin/env python3
###
# GPT KUnit Test Generator Gemini Version
# Author: LTY_CK_TS
# Copyright © 2024 by LTY_CK_TS, All Rights Reserved.
###
import os
import sys

from vertexai.preview.generative_models import GenerativeModel
import toml

global end, config, linux_path

model = GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])


def send_message(msg):
    print("Message sent! Now waiting for reply...")
    response = chat.send_message(msg)
    print("Message received!")
    return response.text


def write_log():
    log = open("message_log.txt", "w")
    for message in chat.history:
        log.write(f'{"-" * 20}\n{message.role}\n{"-" * 20}\n{message.parts[0].text}\n')
    log.close()


def initialise():
    global config, linux_path
    with open("config.toml") as config_file:
        config = toml.load(config_file)

    if not config["LINUX_PATH"]:
        print("ERROR! Please set your LINUX_PATH in config.toml")
        exit(1)
    linux_path = os.path.abspath(config["LINUX_PATH"])
    if not os.path.exists(linux_path) or not os.path.isdir(linux_path):
        print("ERROR! LINUX_PATH not found or not a directory!")
        exit(1)
    print("-------------------------------------")


def error_fixing_mode(text=None):
    print("Entering error fixing mode...")
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
    prompt = (f"Please fix the following errors and return only the fixed code:\n```\n{errors}\n```\n"
              f"You should return the fixed complete code file, make sure the code is inside a ```c block.")
    this_content = send_message(prompt)
    if not this_content:
        print("ERROR! No response received!")
        return ""
    print("---------Generated Code-------------")
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
        print(result_code)
        print("-------------------------------------")
    return result_code


def test_generating_mode(abs_path=None, start_l=None, end_l=None):
    print("Entering test generating mode...")
    file_path = abs_path
    print("Full file path: " + file_path)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        print("ERROR! File not found!")
        exit(1)
    with open(file_path) as file:
        code = file.readlines()
    start_line = start_l
    end_line = end_l
    print("-------------------------------------")
    if start_line > end_line:
        print("ERROR! Start line should be smaller than end line!")
        exit(1)
    code = "".join(code[start_line - 1:end_line])
    template = ("```c\n#include <kunit/test.h>\nstatic void test(struct kunit *test)\n{KUNIT_EXPECT_EQ(test, 1, 1);}\n"
                "static struct kunit_case test_cases[] = {\nKUNIT_CASE(test),\n{}\n"
                "static struct kunit_suite test_suite = {\n.name = \"test_cases\",\n.test_cases = test_cases,\n};\n"
                "kunit_test_suite(test_suite);\nMODULE_LICENSE(\"GPL\");\n```")
    prompt = (f"Please generate a KUnit test file for the following code:\n```c\n{code}\n```\nMake sure you "
              f"do not include any sentences other than the code itself in your reply. You should implement all the "
              f"codes, do not leave any space for the user to add any code or add any comment "
              f"that is not inside the code. Make sure the code is inside a ```c block. "
              f"The lib of KUnit is <kunit/test.h>.\nBelow is a template for the KUnit test file:\n{template}\n")
    this_content = send_message(prompt)
    if not this_content:
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
                           .strip().replace("<linux/kunit/test.h>", "<kunit/test.h>"))
        print(return_code)
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
        print(result[start_pos:])
        print("-------------------------------------")
        error = result[start_pos:]
        debug_times += 1
        print(f"Self-debugging times: {debug_times}")
        result_code = error_fixing_mode(text=error)
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
    print("GPT KUnit Test Generator Gemini Ver")
    if len(sys.argv) > 3:
        initialise()
        abs_path = linux_path + "/" + sys.argv[1]
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            print("ERROR! File not found!")
            exit(1)
        try:
            start_line = int(sys.argv[2])
            end_line = int(sys.argv[3])
        except ValueError:
            print("ERROR! Invalid start line or end line!")
            exit(1)
        max_debug_time = 10
        print(f"Auto mode enabled, max self-debugging times: {max_debug_time}")
        print("Author: LTY_CK_TS")
        print("Version: 0.2.0")
        print("-------------------------------------")
        test_generating_mode(abs_path=abs_path, start_l=start_line, end_l=end_line)
    elif len(sys.argv) > 1:
        print("ERROR! You should specify the path as well as the start line and end line as argument!")
        exit(1)
    print("Exiting...")
