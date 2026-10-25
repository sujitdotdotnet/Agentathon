"""
04 - An LLM Call as a Tool

So far our tools were plain Python (maths, an API). But a tool can
itself call an LLM - useful when the job is a language task (reading,
classifying, or summarising text) that plain code cannot do.

Enterprise example: incident intake. One tool uses an LLM to TRIAGE a raw
report (severity, category, one-line summary). A second, plain tool PAGES the
right on-call team for that severity. The agent orchestrates: triage, page,
then explain what it did.

Run: uv run 04_llm_as_a_tool.py
"""

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please add DEEPSEEK_API_KEY to .env first.")
    exit()

# A small, focused model used INSIDE the triage tool. This is the key idea of
# this file: the tool's own work is an LLM call.
triage_llm = ChatDeepSeek(model="deepseek-chat", temperature=0.0)


@tool
def triage_incident(report: str) -> str:
    """Read a raw incident report and classify it. Returns the severity
    (P1, P2, or P3), a short category, and a one-line summary."""
    instruction = (
        "You are an incident triage engine. Read the report and reply in "
        "exactly this format on one line, plain text:\n"
        "severity=<P1|P2|P3>; category=<one or two words>; summary=<one short line>\n"
        "P1 = major outage or many users blocked. P2 = partial or degraded. "
        "P3 = minor or cosmetic.\n\n"
        "Report: " + report
    )
    return triage_llm.invoke(instruction).content.strip()


@tool
def page_oncall(severity: str) -> str:
    """Page the right people for an incident severity (P1, P2, or P3)."""
    level = severity.upper()
    if "P1" in level:
        return "Paged: senior SRE and the incident manager. Bridge opened."
    if "P2" in level:
        return "Paged: the on-call engineer."
    return "Logged for the next business day. No page raised."


agent = create_agent(
    model="deepseek:deepseek-chat",
    tools=[triage_incident, page_oncall],
    system_prompt="You are an incident intake assistant. First call "
                  "triage_incident on the raw report. Then call page_oncall with "
                  "the severity it returned. Finally, tell the user in plain text "
                  "what the incident is and who was paged. No markdown.",
)


def show_trace(messages):
    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                print("THINK/ACT -> run", call["name"], "with", call["args"])
        elif isinstance(message, ToolMessage):
            print("OBSERVE   ->", message.content)
        elif isinstance(message, AIMessage) and message.content:
            print("ANSWER    ->", message.content.strip())


print("Paste a raw incident report and watch the agent triage and page. Type 'quit' to stop.")
print("Try:  The Payments API returns HTTP 500 on every checkout since 2 PM. Nothing works.")
print("Try:  A button label has a small typo on the settings page.")
while True:
    try:
        report = input("\nReport: ").strip()
    except EOFError:
        break
    if report == "":
        continue
    if report.lower() == "quit" or report.lower() == "exit":
        break
    print("====================================================================")
    result = agent.invoke({"messages": [HumanMessage(content=report)]})
    show_trace(result["messages"])
