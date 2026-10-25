"""
02 - The ReAct Agent (create_agent)

Remember the two gaps from 01 (exact maths and today's date)?
Without tools, the bare LLM failed on large calculations and hallucinated
the date. Here we close both gaps using create_agent.

create_agent is the real workflow. Give it a model, some tools, and a short
instruction, and it runs the whole loop for you: ask the model, run any tool it
wants, feed the result back, and repeat until the answer is ready. That
repeating THINK -> ACT -> OBSERVE loop is what makes it an agent, and the trace
below shows it happening.

Run: uv run 02_react_agent.py
"""

import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please add DEEPSEEK_API_KEY to .env first.")
    exit()

# A couple of small tools so the agent has real choices to make.
@tool
def calculate(expression: str) -> str:
    """Work out a maths expression exactly. Use this for any arithmetic."""
    result = eval(expression, {"__builtins__": {}}, {})
    return str(result)

@tool
def get_today() -> str:
    """Return today's date from the system clock."""
    from datetime import date
    return date.today().strftime("%A, %d %B %Y")

# create_agent builds and runs the whole ReAct loop for you.
agent = create_agent(
    model="deepseek:deepseek-chat",
    tools=[calculate, get_today],
    system_prompt="You are a precise assistant. Always use a tool instead of "
                  "guessing numbers or the date. Reply in plain text, with no "
                  "markdown symbols like ** or #.",
)


# A small helper to print the agent's steps in plain language.
# This is also how you DEBUG an agent: everything it did is in the "messages"
# list it returns. Walk that list and you can see each THINK/ACT and each
# OBSERVE - which is how you find where an agent went wrong.
def show_trace(messages):
    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                print("THINK/ACT -> run", call["name"], "with", call["args"])
        elif isinstance(message, ToolMessage):
            print("OBSERVE   ->", message.content)
        elif isinstance(message, AIMessage) and message.content:
            print("ANSWER    ->", message.content.strip())


# First, demonstrate solving the exact problems from 01 where the bare LLM failed.
print("====================================================================")
print("SOLVING THE GAPS FROM 01 WITH AN AGENT")
print("====================================================================")
print("In 01, the bare LLM failed at exact multiplication (89234 * 41176 * 738)")
print("and had no clock for today's date. Watch the agent solve both:\n")

gap_problem = "What is 89234 times 41176 times 738, and what is today's date?"
print("Question :", gap_problem)
print("--------------------------------------------------------------------")
result = agent.invoke({"messages": [HumanMessage(content=gap_problem)]})
show_trace(result["messages"])
print("====================================================================")
print("Both gaps solved! The agent called calculate and get_today automatically.")
print("====================================================================")

print("\nNow ask the agent something yourself. Type 'quit' to stop.")
print("Try:  What is 89 times 47 divided by 3, and what is today's date?")
while True:
    try:
        question = input("\nYou: ").strip()
    except EOFError:
        break
    if question == "":
        continue
    if question.lower() == "quit" or question.lower() == "exit":
        break
    print("====================================================================")
    # The agent expects a dict with a "messages" list, and returns the same shape.
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    show_trace(result["messages"])
