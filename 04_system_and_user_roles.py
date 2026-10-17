"""
04 - Two Voices: System vs User
===============================
Every message has two parts that do different jobs:

        system  ->  WHO the AI should be   (sets tone and expertise)
        user    ->  WHAT you want done     (the actual task)

Same incident. Same task. We change ONLY the system role, and the answer
changes completely.

RUN:
    uv run 04_system_and_user_roles.py
"""

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please run 00_setup_check.py first.")
    exit()

llm = ChatDeepSeek(model="deepseek-chat", temperature=0.2)

incident = "Checkout API latency rose from 200ms to 4s after the 10:30 deployment. Error rate is 8%."
task = "Summarise this incident: " + incident

# Same task, first as an engineer...
print("====================================================================")
print("ROLE: SRE Engineer")
print("====================================================================")
engineer_messages = [
    SystemMessage(content="You are an SRE engineer. Be technical."),
    HumanMessage(content=task),
]
engineer_result = llm.invoke(engineer_messages)
print(engineer_result.content)

# ...then as a business manager.
print("")
print("====================================================================")
print("ROLE: Business Manager")
print("====================================================================")
manager_messages = [
    SystemMessage(content="You are a business manager. Focus on customer impact."),
    HumanMessage(content=task),
]
manager_result = llm.invoke(manager_messages)
print(manager_result.content)

print("")
print("TRY NEXT: change one system role to 'You are a CFO' and run again.")
