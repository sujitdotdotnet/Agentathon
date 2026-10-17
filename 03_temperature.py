"""
03 - The Creativity Dial (Temperature)
======================================
One number changes how adventurous the model is. Same prompt, run twice.

        temperature 0.0  ->  safe, steady, nearly the same answer every time
        temperature 0.9  ->  creative, varied, different each run

The dial goes from 0 to 2. Use LOW for facts and numbers, HIGH for ideas.

RUN:
    uv run 03_temperature.py
"""

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please run 00_setup_check.py first.")
    exit()

prompt = "Give 3 AI use cases for a finance team that builds daily dashboards. One line each."

print("====================================================================")
print("LOW temperature (0.0) - predictable")
print("====================================================================")
low_llm = ChatDeepSeek(model="deepseek-chat", temperature=0.0)
low_result = low_llm.invoke(prompt)
print(low_result.content)

print("")
print("====================================================================")
print("HIGH temperature (0.9) - more varied")
print("====================================================================")
high_llm = ChatDeepSeek(model="deepseek-chat", temperature=0.9)
high_result = high_llm.invoke(prompt)
print(high_result.content)

print("")
print("TRY NEXT: run this file twice. The LOW answer barely changes; the HIGH")
print("answer changes more. That is the dial doing its job.")
