"""
09 - Capstone: AI Use-Case Discovery Assistant
==============================================
Everything from this mission in ONE small app with a web screen:

    roles + temperature (03,04)  ->  prompt template (06)
    ->  structured output (07)   ->  chain (08)   ->  a Gradio screen

A person types a messy work problem. The app returns a clear, structured plan:
ideas, a recommended first use case, value and complexity scores, data needed,
and first prototype steps.

RUN:
    uv run 09_capstone_use_case_app.py
Then open the http://127.0.0.1:7860 link it prints (Ctrl+click).
"""

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import gradio as gr

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "")
api_key = api_key.strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please run 00_setup_check.py first.")
    exit()

# The shape of the plan we want back (structured output, from file 07).
# 'list[str]' just means "a list of text items".
class UseCasePlan(BaseModel):
    ideas: list[str] = Field(description="five practical AI use-case ideas")
    recommended_use_case: str = Field(description="the single best first pick")
    business_value_score: int = Field(description="value, a number from 1 to 10")
    complexity_score: int = Field(description="difficulty, a number from 1 to 10")
    required_data: list[str] = Field(description="data needed to build it")
    first_prototype_steps: list[str] = Field(description="first concrete steps")

# The reusable prompt (template, from file 06).
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a practical AI transformation consultant. Keep it concrete and doable for a beginner."),
    ("human", "Domain: {domain}\nRole: {role}\nProblem: {problem}\nRepetitive task: {task}\nDesired outcome: {outcome}"),
])


# This function runs when the button is clicked.
def discover(domain, role, problem, task, outcome, creativity):

    # Pick the temperature from the radio choice (plain if / else, the dial from file 03).
    if creativity == "Conservative":
        temperature = 0.1
    elif creativity == "Balanced":
        temperature = 0.3
    else:
        temperature = 0.7

    # prompt -> model with structured output : the chain, from file 08.
    llm = ChatDeepSeek(model="deepseek-chat", temperature=temperature)
    structured_llm = llm.with_structured_output(UseCasePlan)
    chain = prompt | structured_llm

    values = {
        "domain": domain,
        "role": role,
        "problem": problem,
        "task": task,
        "outcome": outcome,
    }

    try:
        plan = chain.invoke(values)
    except Exception as error:
        return "The model call failed. Check internet, API key, or balance.\n\n" + str(error)

    # Build a readable report, one line at a time (plain string joining).
    report = "# AI Use-Case Plan for " + domain + "\n\n"

    report = report + "## Ideas\n"
    for idea in plan.ideas:
        report = report + "- " + idea + "\n"

    report = report + "\n## Recommended first use case\n"
    report = report + plan.recommended_use_case + "\n"

    report = report + "\n**Business value:** " + str(plan.business_value_score) + "/10"
    report = report + "   **Complexity:** " + str(plan.complexity_score) + "/10\n"

    report = report + "\n## Data you will need\n"
    for item in plan.required_data:
        report = report + "- " + item + "\n"

    report = report + "\n## First prototype steps\n"
    step_number = 1
    for step in plan.first_prototype_steps:
        report = report + str(step_number) + ". " + step + "\n"
        step_number = step_number + 1

    return report


# The web screen. Gradio is a quick way to put a UI on Python.
with gr.Blocks(title="AI Use-Case Discovery Assistant") as demo:
    gr.Markdown("# AI Use-Case Discovery Assistant\nDescribe a messy work problem. Get a structured first AI plan.")
    with gr.Row():
        domain = gr.Textbox(label="Domain", value="Logistics")
        role = gr.Textbox(label="Your role", value="Operations Manager")
    problem = gr.Textbox(label="Business problem", value="Shipment delays are handled manually", lines=2)
    task = gr.Textbox(label="Repetitive task", value="Checking carrier updates and writing customer replies", lines=2)
    outcome = gr.Textbox(label="Desired outcome", value="Faster, clearer delay communication", lines=2)
    creativity = gr.Radio(["Conservative", "Balanced", "Creative"], value="Balanced", label="Response style (temperature)")
    button = gr.Button("Generate use-case plan", variant="primary")
    output = gr.Markdown()
    button.click(discover, [domain, role, problem, task, outcome, creativity], output)

# Start the web app (only when run directly: uv run 09_capstone_use_case_app.py).
if __name__ == "__main__":
    demo.launch()
