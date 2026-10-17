"""
02 - Why Use a Framework (LangChain)
====================================
Last file we called the model "by hand". Now the SAME task, two ways, so you
can see why a framework helps. This file runs both.

        Way 1: raw          -> build client, send messages, read answer out
        Way 2: LangChain    -> make the model once, .invoke(), read .content

Same model. Same answer. Fewer moving parts. That is the whole point of a
framework: it hides the wiring so you focus on the prompt.

RUN:
    uv run 02_why_a_framework.py
"""

import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please run 00_setup_check.py first.")
    exit()

question = "Explain what an AI agent is, in one simple sentence."

# ---------- WAY 1: RAW (no framework) --------------------------------------
print("====================================================================")
print("WAY 1 - RAW (the wiring is visible)")
print("====================================================================")
from openai import OpenAI
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
raw_response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": question}],
)
raw_answer = raw_response.choices[0].message.content
print(raw_answer)

# ---------- WAY 2: LANGCHAIN (the framework) -------------------------------
print("")
print("====================================================================")
print("WAY 2 - LANGCHAIN (same result, less code)")
print("====================================================================")
from langchain_deepseek import ChatDeepSeek
llm = ChatDeepSeek(model="deepseek-chat")   # describe the model ONCE
result = llm.invoke(question)               # ask -> this is .invoke()
print(result.content)                       # read the answer

print("")
print("Notice: Way 2 is shorter. You never touch base_url or read through")
print("response.choices[0]. Every file from here uses LangChain.")
