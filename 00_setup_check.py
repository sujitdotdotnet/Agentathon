"""
00 - Setup Check  (RUN THIS FIRST)
==================================
Last time, the first hour was lost to setup errors. This file ends that.

Run it once. If you see "ALL GOOD" at the bottom, you are ready for the whole
mission. If not, it tells you exactly what to fix - in plain English.

HOW TO RUN (inside the mission1 folder):
    uv run 00_setup_check.py

What is `uv`?  It is a tool that installs the right Python packages and runs
your file. `uv sync` = "download the packages this project needs". `uv run
<file>` = "run this file". You only `uv sync` once.
"""

import sys
import os
from dotenv import load_dotenv

print("====================================================================")
print("MISSION 1 - SETUP CHECK")
print("====================================================================")

# We collect every problem we find into this list, then show them at the end.
problems = []

# --- 1. Is the Python version high enough? ---------------------------------
major = sys.version_info.major
minor = sys.version_info.minor
if major < 3 or (major == 3 and minor < 11):
    problems.append("Python 3.11 or higher is needed. You have " +
                    str(major) + "." + str(minor))
else:
    print("[OK] Python version is fine.")

# --- 2. Are the required packages installed? (did `uv sync` work?) ---------
try:
    import dotenv
    import openai
    import langchain_deepseek
    import pydantic
    print("[OK] Packages are installed (uv sync worked).")
except ModuleNotFoundError:
    problems.append("Some packages are missing. Fix: run  uv sync  in this folder.")

# --- 3. Is the API key present? --------------------------------------------
# Your secret key lives in the .env file, NOT in the code. The code reads it
# from there so you never paste your key into a shared file by accident.
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    problems.append("No API key. Open the .env file and set your real DEEPSEEK_API_KEY.")
else:
    print("[OK] API key found in .env.")

# --- 4. One tiny real call, to prove the whole path works ------------------
if len(problems) == 0:
    print("[..] Making one small test call to DeepSeek...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        reply = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Reply with exactly: ready"}],
            max_tokens=5,
        )
        answer = reply.choices[0].message.content
        print("[OK] DeepSeek replied:", answer)
    except Exception as error:
        problems.append("The test call failed. Check internet, key, or balance. " +
                        "Details: " + str(error))

# --- Verdict ---------------------------------------------------------------
print("====================================================================")
if len(problems) == 0:
    print("ALL GOOD - you are ready. Open 01_first_llm_call.py next.")
else:
    print("NOT READY YET - please fix these and run again:")
    number = 1
    for one_problem in problems:
        print("  " + str(number) + ". " + one_problem)
        number = number + 1
print("====================================================================")
