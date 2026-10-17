"""
05 - Streaming: Show Words As They Arrive
=========================================
Normally you wait for the whole answer, then it appears. With streaming, the
text prints piece by piece as the model writes it - like a chat app typing.

The total time is the SAME. It just FEELS faster because reading starts
immediately. Worth it for long answers.

The only change: .stream(...) instead of .invoke(...), and we loop over pieces.

RUN:
    uv run 05_streaming.py
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

llm = ChatDeepSeek(model="deepseek-chat", temperature=0.2)

prompt = "Write a calm, honest customer update: their shipment is delayed by weather. Keep it professional."

print("Watch it arrive live:")
print("")

# The model sends the answer in small pieces. We print each piece as it comes.
# end="" keeps them on the same line; flush=True prints each piece at once.
for piece in llm.stream(prompt):
    print(piece.content, end="", flush=True)

print("")
print("")
print("TRY NEXT: change the prompt to a finance or IT update and run again.")
