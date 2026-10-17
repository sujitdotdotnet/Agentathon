"""
01 - Your First LLM Call
========================
The whole idea in one file:

        you send messages  ->  the model  ->  you get text back

No framework yet. We do it "by hand" so you can see every moving part.

RUN:
    uv run 01_first_llm_call.py
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# --- load the secret key from the .env file --------------------------------
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please run 00_setup_check.py first.")
    exit()

# WHY 'from openai import OpenAI' IF WE ARE USING DEEPSEEK?
# ------------------------------------------------------------------
# DeepSeek accepts the same request format OpenAI made popular. So we reuse
# OpenAI's connection library, but point it at DeepSeek's address (base_url)
# with DeepSeek's key. You are NOT using an OpenAI model here.
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# A "message" has a role and content. Two roles matter for now:
#   system = who the AI should be   |   user = what you are asking
system_message = {"role": "system", "content": "You are a practical AI use-case consultant."}
user_message = {"role": "user", "content": "I work in logistics. We manually explain shipment delays to customers. Give exactly 5 practical AI use cases, 2 short lines each."}

messages = [system_message, user_message]

print("Sending your messages to DeepSeek...")
print("")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    temperature=0.2,   # how creative (the next file explains this dial)
    max_tokens=700,    # a LENGTH LIMIT, not a word count. A "token" is a chunk
                       # of text about 3/4 of a word. 700 tokens is about 500
                       # words. You pay per token, so we cap the length.
)

# The answer is inside the response object. We read it out here.
# (Later, a framework replaces this long line with a single .invoke() call.)
answer = response.choices[0].message.content
print(answer)

print("")
print("TRY NEXT: change 'logistics' to your own industry and run again.")
