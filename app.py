# Vercel entrypoint. The capstone file name starts with a digit, so it cannot be
# imported with a normal "import" statement; load it by path instead.
import importlib.util
from pathlib import Path

import gradio as gr
from fastapi import FastAPI

_path = Path(__file__).parent / "09_capstone_use_case_app.py"
_spec = importlib.util.spec_from_file_location("capstone", _path)
_capstone = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_capstone)

app = gr.mount_gradio_app(FastAPI(), _capstone.demo, path="/")
