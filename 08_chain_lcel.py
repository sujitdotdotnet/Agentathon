"""
08 - Chains: Join The Steps Into One Flow
=========================================
So far each piece worked alone. Now we join them into ONE flow:

        prompt  ->  model  ->  parser
        (build)     (ask)      (clean up the answer to plain text)

The '|' symbol means "send the result of the left into the right". Data goes in
one end, a finished result comes out the other. This joined flow is a "chain".

WHAT DOES  chain = prompt | llm | parser  ACHIEVE?
It saves you from calling each step by hand. You call chain.invoke(...) once,
and the value flows through all three steps for you.

RUN:
    uv run 08_chain_lcel.py
"""

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please run 00_setup_check.py first.")
    exit()

prompt = ChatPromptTemplate.from_template(
    "Score this AI use case from 1 to 10 for business value and 1 to 10 for "
    "complexity. Use case: {use_case}. Answer in short bullet points."
)
llm = ChatDeepSeek(model="deepseek-chat", temperature=0.2)
parser = StrOutputParser()          # pulls clean text out of the model reply

# Here is the pipeline. Read each '|' as the word "then".
chain = prompt | llm | parser

# One call runs all three steps: fill {use_case}, ask the model, clean it up.
values = {"use_case": "An assistant that summarises daily finance dashboard anomalies."}
result = chain.invoke(values)
print(result)

print("")
print("TRY NEXT: change the use_case value and run again - the same chain handles it.")
