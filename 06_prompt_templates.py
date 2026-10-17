"""
06 - Prompt Templates: Write Once, Fill The Blanks
==================================================
Instead of rewriting a prompt every time, write it ONCE with labelled blanks
(the {curly braces}), then fill them with fresh values each run - like a
standard letter that leaves a space for the name.

This is what turns a one-off prompt into a reusable feature.

RUN:
    uv run 06_prompt_templates.py
"""

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please run 00_setup_check.py first.")
    exit()

llm = ChatDeepSeek(model="deepseek-chat", temperature=0.2)

# The blanks are {customer}, {issue}, {tone}, {next_step}. We fill them below.
template = ChatPromptTemplate.from_messages([
    ("system", "You write short, clear customer updates."),
    ("human", "Customer: {customer}\nIssue: {issue}\nTone: {tone}\nNext step: {next_step}\nWrite a 3-line update."),
])

# Fill the blanks with real values...
values = {
    "customer": "Acme Retail",
    "issue": "shipment delayed due to weather",
    "tone": "calm and professional",
    "next_step": "revised ETA shared by 5 PM",
}
filled_prompt = template.invoke(values)

# ...then send the filled prompt to the model.
result = llm.invoke(filled_prompt)
print(result.content)

print("")
print("TRY NEXT: change only the values above (new customer, new issue) and")
print("run again. The template stays the same - that is the reuse.")
