"""
01 - Why LLMs Need Tools

A language model predicts text, so on its own it cannot do exact maths or know
today's date. This file shows both gaps, then shows plain Python getting them
right. Closing those gaps is what tools are for.

Run: uv run 01_why_tools.py
"""

import os
from datetime import date
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

# Load the DeepSeek key from the .env file.
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please add DEEPSEEK_API_KEY to .env first.")
    exit()

llm = ChatDeepSeek(model="deepseek-chat", temperature=0.0)

# Gap 1: exact maths. Big numbers on purpose, since that is where the model slips.
print("====================================================================")
print("GAP 1: exact maths")
print("====================================================================")
a = 89234
b = 41176
c = 738
question = ("What is " + str(a) + " times " + str(b) + " times " + str(c) +
            "? Answer in plain text, digits only, no commas, no markdown.")
llm_answer = llm.invoke(question)
python_answer = a * b * c
print("LLM says      :", llm_answer.content.strip())
print("Python says   :", python_answer)
print("Even when it looks close (or gets lucky), the LLM cannot GUARANTEE the")
print("exact number. A calculator tool always can.")

# Gap 2: real-time facts.
print("")
print("====================================================================")
print("GAP 2: today's date")
print("====================================================================")
llm_date = llm.invoke("What is today's date? Answer in plain text, no markdown.")
python_date = date.today().strftime("%B %d, %Y")
print("LLM says      :", llm_date.content.strip())
print("Python says   :", python_date)
print("The LLM has no clock, so it cannot truly know today's date.")

# Two questions that always come up:
#   "But ChatGPT gets these right." ChatGPT is not a pure model; it already has a
#   calculator, a clock, and web access. Here we call the bare model.
#   "Then why keep the model?" Python does each exact step, but the model decides
#   which step to take, and when, for a request it has not seen before.

print("")
print("THE FIX: let the model use Python functions (tools).")
print("A function can calculate exactly, read the clock, query a database, or")
print("call an API. The model decides which one to use; the function does the")
print("exact work. The next file (02_react_agent.py) shows an agent using")
print("tools to solve both of these gaps.")
