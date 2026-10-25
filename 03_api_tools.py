"""
03 - Tools That Call Web APIs

Tools can also reach the internet. This file gives the agent two web tools: a
weather lookup that chains two calls (find the city's coordinates, then fetch
the forecast), and a live web search for current facts and news. The agent
decides which to use and chains them on its own.

Weather uses Open-Meteo (no key). Search uses serper.dev; add SERPER_API_KEY to
.env to switch it on, or leave it off and the agent uses its other tools.

Run: uv run 03_api_tools.py
"""

import os
import json
import urllib.request
import urllib.parse
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


@tool
def find_coordinates(city: str) -> str:
    """Find the latitude and longitude of a city by its name."""
    url = ("https://geocoding-api.open-meteo.com/v1/search?name="
           + urllib.parse.quote(city) + "&count=1&language=en&format=json")
    try:
        raw = urllib.request.urlopen(url, timeout=8).read()
        data = json.loads(raw)
    except Exception as error:
        return "Could not reach the geocoding service: " + str(error)

    if "results" not in data or len(data["results"]) == 0:
        return "No city found with that name."

    place = data["results"][0]
    return ("latitude " + str(place["latitude"]) +
            ", longitude " + str(place["longitude"]) +
            " (" + place["name"] + ")")


@tool
def get_weather(latitude: float, longitude: float) -> str:
    """Get the current weather for a latitude and longitude."""
    url = ("https://api.open-meteo.com/v1/forecast?latitude=" + str(latitude) +
           "&longitude=" + str(longitude) + "&current_weather=true")
    try:
        raw = urllib.request.urlopen(url, timeout=8).read()
        data = json.loads(raw)
    except Exception as error:
        return "Could not reach the weather service: " + str(error)

    now = data["current_weather"]
    code = int(now["weathercode"])
    raining = code >= 51        # Open-Meteo: codes 51 and up mean drizzle/rain/snow
    return ("temperature " + str(now["temperature"]) + " C, wind " +
            str(now["windspeed"]) + " km/h, raining: " + str(raining))


@tool
def web_search(query: str) -> str:
    """Search the web for current facts, news, or prices."""
    serper_key = os.getenv("SERPER_API_KEY", "").strip()
    if serper_key == "" or serper_key == "your_serper_api_key_here":
        return ("Web search is not configured. Add a SERPER_API_KEY to .env to "
                "switch it on.")
    try:
        request = urllib.request.Request(
            "https://google.serper.dev/search",
            data=json.dumps({"q": query}).encode("utf-8"),
            headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
            method="POST",
        )
        data = json.loads(urllib.request.urlopen(request, timeout=8).read())
    except Exception as error:
        return "Web search failed: " + str(error)
    results = data.get("organic", [])
    if len(results) == 0:
        return "No web results found."
    lines = []
    for item in results[:4]:
        lines.append("- " + str(item.get("title")) + ": " + str(item.get("snippet")))
    return "\n".join(lines)


agent = create_agent(
    model="deepseek:deepseek-chat",
    tools=[find_coordinates, get_weather, web_search],
    system_prompt="You are a travel helper. For weather, first use "
                  "find_coordinates for the city, then get_weather for those "
                  "coordinates, then say whether to carry an umbrella. For "
                  "questions about current facts or news, use web_search. "
                  "Reply in plain text, with no markdown symbols like ** or #.",
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


print("Ask about the weather in a city, or something happening in the world.")
print("Try:  I am travelling to Tokyo. Should I carry an umbrella?")
print("Try:  What is the latest RBI circular? Search the web.")
print("Type 'quit' to stop.")
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
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    show_trace(result["messages"])
