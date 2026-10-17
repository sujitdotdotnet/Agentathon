"""
07 - Structured Output: Fields, Not A Paragraph
===============================================
A paragraph reads nicely but software can't easily use it. Here we ask the
model to fill in a fixed SHAPE of named fields instead.

HOW DOES IT KNOW WHAT TO PUT IN EACH FIELD?
You tell it. Below we list the fields AND describe each one. LangChain sends
that description to the model and makes the reply match. The field name and its
description ARE the instruction - for example 'business_value_score 1 to 10' is
why it returns a number from 1 to 10, not a sentence.

RUN:
    uv run 07_structured_output.py
"""

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from pydantic import BaseModel, Field

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please run 00_setup_check.py first.")
    exit()

# This is the SHAPE we want back. Each line is one field the model must fill.
# It reads like a typed record: "name : type = description".
# The description is the instruction the model reads for that field.
class UseCaseBrief(BaseModel):
    domain: str = Field(description="the business domain")
    problem: str = Field(description="the business problem in one line")
    recommended_use_case: str = Field(description="the single best AI use case")
    business_value_score: int = Field(description="value, a number from 1 to 10")
    complexity_score: int = Field(description="difficulty, a number from 1 to 10")
    first_prototype_step: str = Field(description="the very first step to build")

# .with_structured_output(...) says: "your reply must match this shape."
llm = ChatDeepSeek(model="deepseek-chat", temperature=0.1)
structured_llm = llm.with_structured_output(UseCaseBrief)

messy_text = "I work in logistics. We manually compare carrier rates and write customer delay messages."

brief = structured_llm.invoke(messy_text)

# 'brief' is now a real object with fields - not a blob of text.
print("Recommended use case :", brief.recommended_use_case)
print("Business value score :", brief.business_value_score, "/ 10")
print("Complexity score     :", brief.complexity_score, "/ 10")
print("First prototype step :", brief.first_prototype_step)
