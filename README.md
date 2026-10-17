# Mission 1: From LLM Call to Chain

A hands-on, beginner-friendly walkthrough (AI Agentathon, Mission 1) that goes from a single raw LLM call to a small web app built on a LangChain chain. Each numbered script adds one idea, and the capstone combines them all.

## Summary

You start by calling a model by hand, then learn why a framework helps, how to control creativity and role, how to stream output, how to reuse prompts, how to get structured data back, and how to join everything into a chain. The final app, the **AI Use-Case Discovery Assistant**, takes a messy work problem and returns a structured AI plan: ideas, a recommended first use case, value and complexity scores, required data, and first prototype steps.

**Stack:** Python 3.11+, LangChain, DeepSeek (`deepseek-chat`), Pydantic, Gradio, `uv`.

## Scripts

| File | Concept |
|------|---------|
| `00_setup_check.py` | Verifies your environment and API key. Run this first. |
| `01_first_llm_call.py` | A raw LLM call with the OpenAI-compatible client, no framework. |
| `02_why_a_framework.py` | The same task done raw vs. with LangChain. |
| `03_temperature.py` | The creativity dial: low vs. high temperature. |
| `04_system_and_user_roles.py` | System role (who the AI is) vs. user role (what you want). |
| `05_streaming.py` | Print the answer as it arrives with `.stream()`. |
| `06_prompt_templates.py` | Reusable prompts with fill-in-the-blank variables. |
| `07_structured_output.py` | Pydantic models so the model returns named fields, not a paragraph. |
| `08_chain_lcel.py` | Chain steps with `prompt \| llm \| parser`. |
| `09_capstone_use_case_app.py` | The full Gradio app combining roles, templates, structured output and chains. |
| `app.py` | Vercel entrypoint that exposes the capstone as an ASGI app. |

## Setup

1. Install [uv](https://docs.astral.sh/uv/).
2. Install dependencies:
   ```
   uv sync
   ```
3. Create a `.env` file in this folder with your DeepSeek key:
   ```
   DEEPSEEK_API_KEY=your_key_here
   ```
   Never commit this file. Keep it in `.gitignore`.
4. Check everything works:
   ```
   uv run 00_setup_check.py
   ```
   You should see "ALL GOOD".

## Run

Run any step with `uv run <file>`, for example:

```
uv run 01_first_llm_call.py
uv run 09_capstone_use_case_app.py
```

The capstone prints a local link (http://127.0.0.1:7860). Open it in your browser.

## Deploy to Vercel

`pyproject.toml` sets the entrypoint to `app:app`. `app.py` loads the capstone and mounts the Gradio UI on a FastAPI app.

1. Push the repo and import it in Vercel.
2. Add `DEEPSEEK_API_KEY` under Project Settings → Environment Variables. The `.env` file is not deployed.
3. Deploy.

## License

See [LICENSE](LICENSE).
