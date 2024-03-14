# This is a beta version of merging two models.

from gpt_4 import send_message as gpt_4_send_message

import toml
import openai
import sys
import requests
import json
import os
from vertexai.preview.generative_models import GenerativeModel


# model = "@hf/thebloke/codellama-7b-instruct-awq"  # codellama-7b-instruct-awq model from Meta via Hugging Face
model = "@hf/thebloke/deepseek-coder-6.7b-instruct-awq"  # deepseek-coder with instruct-awq model from Hugging Face
max_debug_time = 10  # Max self-debugging times

second_model = "gemini"
# second_model = "gpt-4"


def workers_ai_send_message(history, msg):
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
                    print("ERROR! JSON decode error!")
                    exit(1)
    history.append({"role": "system", "content": response_text})
    return response_text

def gemini_send_message(msg):
    print("Message sent! Now waiting for reply...")
    response = gemini_chat.send_message(msg)
    print("Message received!")
    return [response.text]

def error_fixing_mode(errors):
    if second_model == "gpt-4":
        received_content = gpt_4_send_message(client, thread, assistant, errors)
    elif second_model == "gemini":
        prompt = (f"Please fix the following errors and return only the fixed code:\n```\n{errors}\n```\n"
                  f"You should return the fixed complete code file, make sure the code is inside a ```c block.")
        received_content = gemini_send_message(prompt)
    else:
        print("ERROR! Invalid second model!")
        return ""

    if not received_content:
        print("ERROR! No response received!")
        return ""
    result_code = ""
    print("---------Generated Code-------------")
    for this_content in received_content:
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
                return ""
            else:
                result_code = (this_content[start_pos + 4:end_pos].strip())
        print(result_code)
        print("-------------------------------------")
    return result_code


if len(sys.argv) < 2:
    print("Usage: python3 model_merge.py <function name>")
    exit(1)
try:
    func_name = sys.argv[1]
    help_text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
except ValueError:
    print("ERROR! Invalid input!")
    exit(1)
with open("config.toml") as config_file:
    config = toml.load(config_file)
if not config["CF_API_KEY"]:
    print("ERROR! Please set your CF_API_KEY in config.toml")
    exit(1)
if not config["CF_ACCOUNT_ID"]:
    print("ERROR! Please set your CF_ACCOUNT_ID in config.toml")
    exit(1)
account_id = config["CF_ACCOUNT_ID"]
api_token = config["CF_API_KEY"]
if second_model == "gpt-4" and not config["OPENAI_API_KEY"]:
    print("ERROR! Please set your OPENAI_API_KEY in config.toml")
    exit(1)
if not config["LINUX_PATH"]:
    print("ERROR! Please set your LINUX_PATH in config.toml")
    exit(1)
linux_path = os.path.abspath(config["LINUX_PATH"])

if second_model == "gpt-4":
    client = openai.Client(api_key=config["OPENAI_API_KEY"])
    if not config["ASSISTANT_ID"]:
        print("No existing assistant found. Now creating new assistant...")
        assistant = client.beta.assistants.create(name="KUnit-2Phase",
                                                  instructions="You are a developer who is very familiar with the "
                                                               "KUnit tests in Linux kernel.\nUser will send you "
                                                               "pieces of pseudocode. You should write executable KUnit "
                                                               "file for those code. User may also send you errors "
                                                               "that occur when running, you should fix the errors "
                                                               "and send back the fixed complete code.\nDo not include "
                                                               "any sentences other than the code itself in your "
                                                               "reply. You should implement all the codes, do not "
                                                               "leave any space for the user to add any code.\nYou must"
                                                               "contain your code between \"```c\" and \"```\"."
                                                               "The lib of KUnit is <kunit/test.h>",
                                                  tools=[],
                                                  model="gpt-4-turbo-preview")
        with open("config.toml", "w") as config_file:
            config["ASSISTANT_ID"] = assistant.id
            toml.dump(config, config_file)
    else:
        assistant_id = config["ASSISTANT_ID"]
        assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
    if not config["THREAD_ID"]:
        print("No existing thread found. Now creating new thread...")
        thread = client.beta.threads.create()
        with open("config.toml", "w") as config_file:
            config["THREAD_ID"] = thread.id
            toml.dump(config, config_file)
    else:
        delete_thread = client.beta.threads.delete(thread_id=config["THREAD_ID"])
        if not delete_thread.deleted:
            print(f"ERROR! Failed to delete thread {config['THREAD_ID']}!")
            exit(1)
        print("Thread deleted! Now creating new thread...")
        thread = client.beta.threads.create()
        with open("config.toml", "w") as config_file:
            config["THREAD_ID"] = thread.id
            toml.dump(config, config_file)
elif second_model == "gemini":
    gemini_model = GenerativeModel("gemini-pro")
    gemini_chat = gemini_model.start_chat(history=[])
else:
    print("ERROR! Invalid second model!")
    exit(1)

history = []
prompt = (f"I want you to generate some unit tests in pseudocode for the function ```{func_name}``` in Linux kernel. "
          "Only return the unit tests, do not return the function itself. Make it short and simple. "
          "You should implement all the codes. Make sure to contain the tests between \"```c\" and \"```\".")
if help_text:
    prompt += f"\n{help_text}"
pseudo_code = workers_ai_send_message(history, prompt)

if pseudo_code[:4] == "```c" and pseudo_code[-3:] == "```":
    pseudo_code = pseudo_code[4:-4].strip()
else:
    start_pos = pseudo_code.find("```c")
    end_pos = pseudo_code.rfind("```")
    if start_pos == end_pos:
        pseudo_code = pseudo_code[start_pos + 4:].strip()
    elif start_pos == -1 or end_pos == -1:
        print(pseudo_code)
        print("-------------------------------------")
        print("ERROR! No code found in this response!")
        print("-------------------------------------")
        exit(1)
    else:
        pseudo_code = pseudo_code[start_pos + 4:end_pos].strip()

if second_model == "gpt-4":
    received_content = gpt_4_send_message(client, thread, assistant, pseudo_code)
elif second_model == "gemini":
    template = ("```c\n#include <kunit/test.h>\nstatic void test(struct kunit *test)\n{KUNIT_EXPECT_EQ(test, 1, 1);}\n"
                "static struct kunit_case test_cases[] = {\nKUNIT_CASE(test),\n{}\n"
                "static struct kunit_suite test_suite = {\n.name = \"test_cases\",\n.test_cases = test_cases,\n};\n"
                "kunit_test_suite(test_suite);\nMODULE_LICENSE(\"GPL\");\n```")
    prompt = (f"Please generate a KUnit test file for the following function:\n```c\n{func_name}\n```\nMake sure you "
              f"do not include any sentences other than the code itself in your reply. You should implement all the "
              f"codes, do not leave any space for the user to add any code or add any comment "
              f"that is not inside the code. Make sure the code is inside a ```c block. "
              f"The lib of KUnit is <kunit/test.h>.\nBelow is a template for the KUnit test file:\n{template}\n")
    received_content = gemini_send_message(prompt)
else:
    print("ERROR! Invalid second model!")
    exit(1)
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
            return_code = (this_content[start_pos + 4:end_pos].strip())
            code_found = True
    print(return_code)
    print("-------------------------------------")
if not code_found:
    print("ERROR! No code found in all the responses! Exiting...")
    exit(1)

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
if (error_pos != -1 or fail_pos != -1) and result.find("unsatisfied dependencies") != -1:
    print("-------------------------------------")
    print("ERROR! Unsatisfied dependencies! Please check dependencies yourself!")
    print("The test file is located at: " + test_file)
    print("-------------------------------------")
    exit(1)

debug_times = 0
start_pos = error_pos if error_pos != -1 else fail_pos
while start_pos != -1:
    if debug_times >= max_debug_time:
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
    result_code = error_fixing_mode(errors=error)
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
print("-------------------------------------")
print("All tests passed! Congratulations!")
print("The test file is located at: " + test_file)
print("-------------------------------------")
