import openai
import os
import json

with open("config.json") as config_file:
    config = json.load(config_file)

openai.api_key = config["OPENAI_API_KEY"]

assistant_id = "asst_ywt0k3pR1SH34G9MJf80TM6D"
assistant = openai.beta.assistants.retrieve(assistant_id=assistant_id)

print(assistant.model)