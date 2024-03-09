from gpt_4 import send_message as gpt_4_send_message
from workers_ai_blackbox import send_message as workers_ai_send_message
import toml
import openai
import sys


if len(sys.argv) < 2:
    print("Usage: python3 two-phase.py <function name>")
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
if not config["OPENAI_API_KEY"]:
    print("ERROR! Please set your OPENAI_API_KEY in config.toml")
    exit()

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

history = []
prompt = (
        f"I want you to generate a test file in pseudocode for the function ```{func_name}``` in Linux kernel."
        "Do not include any sentences other than the code itself in your reply. You should implement all the codes. "
        "Make sure to contain your code between \"```c\" and \"```\".")
if help_text:
    prompt += f"\n{help_text}"
