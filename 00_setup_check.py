"""
00 - Setup Check  (RUN THIS FIRST)
==================================
Run this once. If you see "ALL GOOD" at the
bottom, you are ready for the whole mission. If not, it tells you exactly what
to fix - in plain English.

HOW TO RUN (inside the mission2 folder):
    uv run 00_setup_check.py

If `uv` is not recognised, install it with:  pip install uv
Keep this project OUT of a OneDrive/Dropbox-synced folder - cloud sync can break
package installs (the "os error 396" hardlink error).
"""

import sys
import os
from dotenv import load_dotenv

print("====================================================================")
print("MISSION 2 - SETUP CHECK")
print("====================================================================")

problems = []

# 1. Python version (3.11 or higher is required).
major = sys.version_info.major
minor = sys.version_info.minor
if major < 3 or (major == 3 and minor < 11):
    problems.append("Python 3.11 or higher is needed. You have " +
                    str(major) + "." + str(minor) + ". Install 3.11+ and re-run.")
else:
    print("[OK] Python version is fine.")

# 2. Packages installed? (did uv sync work?)
try:
    import dotenv
    import langchain
    import langchain_deepseek
    import gradio
    import pydantic
    print("[OK] Packages are installed (uv sync worked).")
except ModuleNotFoundError:
    problems.append("Some packages are missing. Fix: run  uv sync  in this folder.")

# 3. Is the API key present?
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    problems.append("No API key. Open the .env file and set your real DEEPSEEK_API_KEY.")
else:
    print("[OK] API key found in .env.")

# 4. One tiny real call, to prove the whole path works.
if len(problems) == 0:
    print("[..] Making one small test call to DeepSeek...")
    try:
        from langchain_deepseek import ChatDeepSeek
        llm = ChatDeepSeek(model="deepseek-chat", temperature=0.0, max_tokens=5)
        reply = llm.invoke("Reply with exactly: ready")
        print("[OK] DeepSeek replied:", reply.content.strip())
    except Exception as error:
        problems.append("The test call failed. Check internet, key, or balance. " +
                        "Details: " + str(error))

# Verdict.
print("====================================================================")
if len(problems) == 0:
    print("ALL GOOD - you are ready. Open 01_why_tools.py next.")
else:
    print("NOT READY YET - please fix these and run again:")
    number = 1
    for one_problem in problems:
        print("  " + str(number) + ". " + one_problem)
        number = number + 1
print("====================================================================")
