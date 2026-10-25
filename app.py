"""
VulnGuard-ReAct: Autonomous Cybersecurity Vulnerability Intelligence & Remediation Agent
A full-stack Gradio application demonstrating an advanced ReAct agent powered by create_agent,
real free APIs (OSV.dev, CISA KEV, Serper), algorithmic scoring, and LLM mock/simulation tools.
"""

import os
import json
import requests
import gradio as gr
from dotenv import load_dotenv
from fastapi import FastAPI

import tools
import agent

load_dotenv()

# Pre-fetch or cache CISA KEV records for rapid dashboard search
CISA_DATA = []
try:
    cisa_resp = requests.get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", timeout=10)
    if cisa_resp.status_code == 200:
        CISA_DATA = cisa_resp.json().get("vulnerabilities", [])
except Exception as e:
    print(f"Warning: Failed to pre-fetch CISA KEV: {e}")

TOTAL_KEV_COUNT = len(CISA_DATA) if CISA_DATA else 1756
RANSOMWARE_KEV_COUNT = sum(1 for v in CISA_DATA if v.get("knownRansomwareCampaignUse") == "Known") if CISA_DATA else 361

# Sample code snippets for Tab 2
CODE_PRESETS = {
    "Python: SQL Injection in FastAPI/SQLAlchemy": {
        "lang": "python",
        "code": """from fastapi import FastAPI, HTTPException
import sqlite3

app = FastAPI()

@app.get("/user_profile")
def get_user(username: str):
    conn = sqlite3.connect("production.db")
    cursor = conn.cursor()
    # Insecure string interpolation allows authentication bypass and data exfiltration
    query = f"SELECT id, username, email, role FROM users WHERE username = '{username}'"
    cursor.execute(query)
    record = cursor.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": record}
"""
    },
    "Python: Insecure Object Deserialization (Pickle)": {
        "lang": "python",
        "code": """import base64
import pickle
from flask import Flask, request

app = Flask(__name__)

@app.route("/restore_session", methods=["POST"])
def restore_session():
    # Insecure deserialization: user-controlled base64 pickle data leads directly to Arbitrary Code Execution
    raw_cookie = request.cookies.get("session_payload")
    if raw_cookie:
        session_data = pickle.loads(base64.b64decode(raw_cookie))
        return f"Welcome back, {session_data.get('user')}"
    return "No session found", 400
"""
    },
    "Node.js: Remote Command Injection (child_process)": {
        "lang": "javascript",
        "code": """const express = require('express');
const { exec } = require('child_process');
const app = express();

app.get('/api/ping', (req, res) => {
    const host = req.query.host;
    // Unsanitized shell command injection: e.g. host = '127.0.0.1; cat /etc/passwd'
    exec(`ping -c 2 ${host}`, (err, stdout, stderr) => {
        if (err) return res.status(500).send(stderr);
        res.send(stdout);
    });
});
"""
    },
    "Python: Server-Side Request Forgery (SSRF)": {
        "lang": "python",
        "code": """import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/fetch_webhook_metadata", methods=["POST"])
def fetch_metadata():
    target_url = request.json.get("webhook_url")
    # Untrusted URL fetch without IP allowlisting allows internal network port scanning or cloud metadata access (169.254.169.254)
    response = requests.get(target_url, timeout=5)
    return jsonify({"status": response.status_code, "body": response.text[:500]})
"""
    },
    "JavaScript: Prototype Pollution": {
        "lang": "javascript",
        "code": """// Insecure deep merge without Object.prototype guard
function merge(target, source) {
    for (let key in source) {
        if (typeof target[key] === 'object' && typeof source[key] === 'object') {
            merge(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}

// User-supplied payload: {"__proto__": {"isAdmin": true}}
app.post('/api/settings', (req, res) => {
    let userSettings = {};
    merge(userSettings, req.body);
    res.json({ message: "Settings saved", settings: userSettings });
});
"""
    }
}

CUSTOM_CSS = """
:root {
    --primary: #00f0ff;
    --primary-hover: #00c8d6;
    --accent: #10b981;
    --danger: #ef4444;
}

body, .gradio-container {
    background-color: #0b0f19 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #e2e8f0;
}

/* Glassmorphic cards */
.vuln-card {
    background: rgba(17, 24, 39, 0.75) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

.metric-box {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.5) 100%);
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: 10px;
    padding: 14px;
    text-align: center;
}

.trace-panel {
    background: #0d1322 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    padding: 12px !important;
    max-height: 520px;
    overflow-y: auto;
}

/* Headers and Badges */
.vuln-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-critical { background: #991b1b; color: #fecaca; border: 1px solid #ef4444; }
.badge-high { background: #9a3412; color: #fed7aa; border: 1px solid #f97316; }
.badge-medium { background: #854d0e; color: #fef08a; border: 1px solid #eab308; }
.badge-low { background: #1e3a8a; color: #bfdbfe; border: 1px solid #3b82f6; }
"""

# -------------------------------------------------------------------------
# Event Handlers
# -------------------------------------------------------------------------

def chat_agent_response(user_message, chat_history):
    if not user_message or not user_message.strip():
        yield chat_history, "", "*Awaiting input...*"
        return

    # Add user message to history
    new_history = list(chat_history) if chat_history else []
    new_history.append({"role": "user", "content": user_message})
    
    # Initialize placeholder assistant turn
    new_history.append({"role": "assistant", "content": "Thinking and selecting tools..."})
    yield new_history, "", "*ReAct loop active: Analyzing query, selecting tools, and gathering telemetry...*"

    # Run agent streaming
    for trace_markdown, partial_response in agent.run_agent_streaming(user_message, chat_history):
        if partial_response:
            new_history[-1]["content"] = partial_response
        yield new_history, "", trace_markdown


def load_code_preset(preset_name):
    data = CODE_PRESETS.get(preset_name, {"lang": "python", "code": ""})
    return data["code"], data["lang"]


def run_code_scan_remediation(code_text, language):
    if not code_text or not code_text.strip():
        return "⚠️ Please paste or select a code snippet first.", "", "*No code provided.*"

    trace_log = []
    trace_log.append("### 🧠 Step 1: Initiating ReAct Code Security Audit")
    trace_log.append(f"> **Action:** Performing Static Application Security Testing (SAST) on `{language}` snippet.")

    # Call SAST tool
    sast_result = tools.analyze_code_vulnerabilities.invoke({"code_snippet": code_text, "language": language})
    trace_log.append(f"#### 📥 Observation from `analyze_code_vulnerabilities`\n```markdown\n{sast_result[:600]}...\n```")

    trace_log.append("### 🧠 Step 2: Generating Hardened Production-Grade Code Patch")
    trace_log.append("> **Action:** Calling `generate_remediation_patch` with defense-in-depth principles.")

    # Call Remediation tool
    remediation_result = tools.generate_remediation_patch.invoke({
        "vulnerability_description": "Vulnerabilities detected by SAST analysis",
        "code_or_config": code_text,
        "language": language
    })
    trace_log.append("#### 📥 Observation from `generate_remediation_patch`\n*Secure replacement generated with assertions and defensive controls.*")

    trace_log.append("### 🎯 Step 3: Triage Complete")
    full_trace = "\n\n---\n\n".join(trace_log)

    return sast_result, remediation_result, full_trace


def filter_cisa_kev(search_query, ransomware_only):
    if not CISA_DATA:
        return [["No data", "Could not load CISA catalog", "-", "-", "-", "-"]]

    filtered = []
    q = (search_query or "").strip().lower()

    for item in CISA_DATA:
        cve = item.get("cveID", "")
        vendor = item.get("vendorProject", "")
        prod = item.get("product", "")
        vuln_name = item.get("vulnerabilityName", "")
        date_added = item.get("dateAdded", "")
        rw = item.get("knownRansomwareCampaignUse", "Unknown")

        if ransomware_only and rw != "Known":
            continue

        if q:
            match_str = f"{cve} {vendor} {prod} {vuln_name}".lower()
            if q not in match_str:
                continue

        filtered.append([
            cve,
            vendor,
            prod,
            vuln_name[:60] + ("..." if len(vuln_name) > 60 else ""),
            date_added,
            "🚨 YES (Known)" if rw == "Known" else "No / Unknown"
        ])

        if len(filtered) >= 100:  # Display top 100 matches
            break

    return filtered if filtered else [["No matches", "Try a different search term", "-", "-", "-", "-"]]


def calculate_cvss_ui(av, ac, pr, ui, s, c, i, a):
    # Map friendly names to 1-letter codes
    av_code = av.split("(")[-1].strip(")")
    ac_code = ac.split("(")[-1].strip(")")
    pr_code = pr.split("(")[-1].strip(")")
    ui_code = ui.split("(")[-1].strip(")")
    s_code = s.split("(")[-1].strip(")")
    c_code = c.split("(")[-1].strip(")")
    i_code = i.split("(")[-1].strip(")")
    a_code = a.split("(")[-1].strip(")")

    result = tools.calculate_cvss_score.invoke({
        "attack_vector": av_code,
        "attack_complexity": ac_code,
        "privileges_required": pr_code,
        "user_interaction": ui_code,
        "scope": s_code,
        "confidentiality": c_code,
        "integrity": i_code,
        "availability": a_code
    })
    return result


def trigger_cve_triage(cve_input):
    msg = f"Perform a comprehensive security triage for {cve_input}: check OSV intelligence, verify CISA KEV status, search recent threat bulletins, and summarize executive remediation."
    return msg


# -------------------------------------------------------------------------
# Build Gradio UI
# -------------------------------------------------------------------------
with gr.Blocks(title="VulnGuard-ReAct | Cybersecurity AI Agent") as demo:
    gr.HTML("""
    <div style="border-bottom: 1px solid rgba(0, 240, 255, 0.2); padding-bottom: 16px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div>
                <h1 style="color: #00f0ff; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">
                    🛡️ VulnGuard-ReAct
                </h1>
                <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 14px;">
                    Autonomous Cybersecurity Vulnerability Intelligence, Triage & Remediation Agent
                </p>
            </div>
            <div style="display: flex; gap: 10px; font-size: 12px; flex-wrap: wrap;">
                <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; color: #34d399; padding: 4px 10px; border-radius: 6px;">
                    ● LangChain create_agent (ReAct)
                </span>
                <span style="background: rgba(0, 240, 255, 0.15); border: 1px solid #00f0ff; color: #38bdf8; padding: 4px 10px; border-radius: 6px;">
                    ● OSV.dev Public API
                </span>
                <span style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; color: #f87171; padding: 4px 10px; border-radius: 6px;">
                    ● CISA KEV (1,756 Exploits)
                </span>
                <span style="background: rgba(168, 85, 247, 0.15); border: 1px solid #a855f7; color: #c084fc; padding: 4px 10px; border-radius: 6px;">
                    ● Live Serper Intel Search
                </span>
            </div>
        </div>
    </div>
    """)

    with gr.Tabs() as tabs:
        
        # -------------------------------------------------------------
        # Tab 1: Interactive ReAct Security Copilot
        # -------------------------------------------------------------
        with gr.Tab("💬 ReAct Security Copilot", id="tab_chat"):
            gr.Markdown("Interact directly with the autonomous ReAct agent. Watch the **Thought & Tool Execution Trace** in real time as it queries live vulnerability APIs, CISA KEV, and static analysis tools.")
            
            with gr.Row():
                with gr.Column(scale=7):
                    chatbot = gr.Chatbot(
                        label="Security Triage Conversation",
                        height=540,
                        avatar_images=(None, "https://api.iconify.design/lucide:shield-alert.svg?color=%2300f0ff")
                    )
                    
                    with gr.Row():
                        user_input = gr.Textbox(
                            placeholder="Ask about a CVE, audit a package (e.g. 'audit jinja2 2.11.2 on PyPI'), or paste a vulnerability scenario...",
                            label="Your Security Query / Instruction",
                            lines=2,
                            scale=8
                        )
                        send_btn = gr.Button("🚀 Submit Query", variant="primary", scale=2)
                    
                    with gr.Row():
                        clear_btn = gr.Button("🧹 Clear Conversation", size="sm")

                    gr.Markdown("#### 💡 Quick Incident & Vulnerability Investigation Presets:")
                    with gr.Row():
                        btn_preset1 = gr.Button("🚨 Audit XZ Backdoor (CVE-2024-3094)", size="sm")
                        btn_preset2 = gr.Button("💥 Triage Log4Shell (CVE-2021-44228)", size="sm")
                        btn_preset3 = gr.Button("📦 Audit PyPI: jinja2==2.11.2", size="sm")
                    with gr.Row():
                        btn_preset4 = gr.Button("⚡ SQLi Code Audit & Patch", size="sm")
                        btn_preset5 = gr.Button("🌐 Live Intel: Spring 0-Day Search", size="sm")
                        btn_preset6 = gr.Button("🧪 Simulate API Gateway 0-Day Drill", size="sm")

                with gr.Column(scale=5):
                    gr.Markdown("### 🧠 ReAct Thought & Tool Execution Trace")
                    gr.Markdown("Observe the agent's internal cognitive loop: **Reasoning (Thought) ➔ Action (Tool Call) ➔ Observation (API Data) ➔ Final Synthesis**.")
                    trace_box = gr.Markdown(
                        value="*Awaiting user query. Once submitted, each step of the ReAct thought loop will appear here live.*",
                        elem_classes=["trace-panel"]
                    )

            # Wiring Tab 1 events
            def send_query(msg, hist):
                return chat_agent_response(msg, hist)

            send_btn.click(
                chat_agent_response,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input, trace_box]
            )
            user_input.submit(
                chat_agent_response,
                inputs=[user_input, chatbot],
                outputs=[chatbot, user_input, trace_box]
            )
            clear_btn.click(lambda: ([], "", "*Trace reset.*"), outputs=[chatbot, user_input, trace_box])

            # Preset buttons wire to input and trigger run
            btn_preset1.click(
                lambda: "Investigate the XZ Utils Backdoor (CVE-2024-3094): fetch official OSV database details, verify if it is listed on CISA KEV, and summarize the backdoor mechanism and remediation.",
                outputs=[user_input]
            )
            btn_preset2.click(
                lambda: "Perform a complete emergency triage for Log4Shell (CVE-2021-44228): verify its CISA KEV listing and ransomware linkage, calculate its official CVSS score, and detail immediate defensive mitigation steps.",
                outputs=[user_input]
            )
            btn_preset3.click(
                lambda: "Audit the open-source package 'jinja2' version '2.11.2' on the 'PyPI' ecosystem using the OSV database. List all discovered vulnerabilities, severities, and the recommended upgrade version.",
                outputs=[user_input]
            )
            btn_preset4.click(
                lambda: "Analyze this insecure code snippet for SQL Injection: `cursor.execute(f'SELECT * FROM users WHERE username = \\'{username}\\' AND password = \\'{password}\\'')`. Perform static code analysis, identify the CWE, and generate a secure parameterized patch.",
                outputs=[user_input]
            )
            btn_preset5.click(
                lambda: "Search live threat intelligence for recent Spring Framework vulnerabilities and zero-day advisories, and report top vendor bulletins and defensive mitigations.",
                outputs=[user_input]
            )
            btn_preset6.click(
                lambda: "Simulate an emerging zero-day threat intelligence advisory for a security tabletop exercise focusing on an unauthenticated JWT signature bypass in Kubernetes API Gateways.",
                outputs=[user_input]
            )

        # -------------------------------------------------------------
        # Tab 2: Code & Dependency Scanner & Patch Studio
        # -------------------------------------------------------------
        with gr.Tab("🔍 Code & Dependency Scanner", id="tab_scanner"):
            gr.Markdown("Submit code snippets or select known vulnerable architectural patterns. The ReAct agent performs automated SAST security analysis, identifies CWEs, and generates production-ready defensive code patches.")
            
            with gr.Row():
                with gr.Column(scale=4):
                    code_preset_dropdown = gr.Dropdown(
                        choices=list(CODE_PRESETS.keys()),
                        value="Python: SQL Injection in FastAPI/SQLAlchemy",
                        label="Select Vulnerability Pattern Preset"
                    )
                    code_lang = gr.Dropdown(
                        choices=["python", "javascript", "go", "java", "c", "cpp", "php"],
                        value="python",
                        label="Source Language"
                    )
                    code_input = gr.Code(
                        value=CODE_PRESETS["Python: SQL Injection in FastAPI/SQLAlchemy"]["code"],
                        language="python",
                        label="Insecure Source Code to Audit",
                        lines=18
                    )
                    scan_btn = gr.Button("🛡️ Analyze Vulnerabilities & Generate Patch", variant="primary")

                with gr.Column(scale=8):
                    with gr.Tabs():
                        with gr.Tab("🚨 Static Security Assessment (SAST)"):
                            sast_output = gr.Markdown("Click **Analyze Vulnerabilities & Generate Patch** to review findings.")
                        with gr.Tab("🛠️ Hardened Defensive Code Patch"):
                            patch_output = gr.Markdown("Hardened production code and verification tests will be rendered here.")
                        with gr.Tab("🧠 Audit Execution Trace"):
                            scan_trace_output = gr.Markdown("Execution steps will appear here.")

            code_preset_dropdown.change(
                load_code_preset,
                inputs=[code_preset_dropdown],
                outputs=[code_input, code_lang]
            )
            scan_btn.click(
                run_code_scan_remediation,
                inputs=[code_input, code_lang],
                outputs=[sast_output, patch_output, scan_trace_output]
            )

        # -------------------------------------------------------------
        # Tab 3: Live CISA KEV Threat Radar
        # -------------------------------------------------------------
        with gr.Tab("📡 Live CISA KEV Threat Radar", id="tab_kev"):
            gr.Markdown("Real-time feed from the **United States CISA Known Exploited Vulnerabilities (KEV) Catalog**. These are vulnerabilities with confirmed in-the-wild weaponized exploitation against enterprises and government networks.")
            
            with gr.Row():
                with gr.Column(scale=4):
                    gr.HTML(f"""
                    <div class="metric-box">
                        <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase;">Total Actively Exploited CVEs</div>
                        <div style="font-size: 32px; font-weight: 800; color: #ef4444; margin: 4px 0;">{TOTAL_KEV_COUNT}</div>
                        <div style="font-size: 11px; color: #cbd5e1;">Tracked by US Federal Cybersecurity Agency</div>
                    </div>
                    """)
                with gr.Column(scale=4):
                    gr.HTML(f"""
                    <div class="metric-box">
                        <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase;">Known Ransomware Campaigns</div>
                        <div style="font-size: 32px; font-weight: 800; color: #f97316; margin: 4px 0;">{RANSOMWARE_KEV_COUNT}</div>
                        <div style="font-size: 11px; color: #cbd5e1;">Actively used in extortion & ransomware attacks</div>
                    </div>
                    """)
                with gr.Column(scale=4):
                    gr.HTML("""
                    <div class="metric-box">
                        <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase;">Mandatory Remediation Rule</div>
                        <div style="font-size: 18px; font-weight: 700; color: #38bdf8; margin: 10px 0;">BOD 22-01 Enforced</div>
                        <div style="font-size: 11px; color: #cbd5e1;">Federal agencies must remediate by specified deadlines</div>
                    </div>
                    """)

            with gr.Row():
                cisa_search = gr.Textbox(
                    placeholder="Search by Vendor (e.g. 'Apache', 'Microsoft', 'Cisco', 'Fortinet') or CVE (e.g. 'CVE-2024-3094')...",
                    label="Filter CISA KEV Catalog",
                    scale=8
                )
                cisa_ransomware_check = gr.Checkbox(label="🚨 Ransomware Campaigns Only", value=False, scale=4)
                cisa_refresh_btn = gr.Button("🔍 Apply Filter", scale=2)

            kev_dataframe = gr.Dataframe(
                headers=["CVE ID", "Vendor / Project", "Product", "Vulnerability Name", "Date Added", "Ransomware Link"],
                value=filter_cisa_kev("", False),
                interactive=False,
                wrap=True
            )

            with gr.Row():
                selected_cve_input = gr.Textbox(
                    placeholder="Enter CVE ID to send to ReAct Agent for deep triage (e.g. CVE-2021-44228)...",
                    label="Triage CVE with Agent",
                    scale=9
                )
                triage_cve_btn = gr.Button("🚀 Send to Agent Tab", variant="primary", scale=3)

            cisa_refresh_btn.click(
                filter_cisa_kev,
                inputs=[cisa_search, cisa_ransomware_check],
                outputs=[kev_dataframe]
            )
            cisa_search.submit(
                filter_cisa_kev,
                inputs=[cisa_search, cisa_ransomware_check],
                outputs=[kev_dataframe]
            )
            cisa_ransomware_check.change(
                filter_cisa_kev,
                inputs=[cisa_search, cisa_ransomware_check],
                outputs=[kev_dataframe]
            )

            # When clicking Triage CVE, copy prompt to chat input and switch tab
            triage_cve_btn.click(
                trigger_cve_triage,
                inputs=[selected_cve_input],
                outputs=[user_input]
            )

        # -------------------------------------------------------------
        # Tab 4: Mathematical CVSS v3.1 Matrix & Calculator
        # -------------------------------------------------------------
        with gr.Tab("🧮 CVSS v3.1 Scoring Engine", id="tab_cvss"):
            gr.Markdown("Calculate official **FIRST Common Vulnerability Scoring System (CVSS v3.1)** base vectors, severity ratings, and impact metrics.")
            
            with gr.Row():
                with gr.Column(scale=6):
                    gr.Markdown("#### 🎯 Exploitability Metrics")
                    cvss_av = gr.Radio(
                        choices=["Network (N)", "Adjacent (A)", "Local (L)", "Physical (P)"],
                        value="Network (N)",
                        label="Attack Vector (AV)"
                    )
                    cvss_ac = gr.Radio(
                        choices=["Low (L)", "High (H)"],
                        value="Low (L)",
                        label="Attack Complexity (AC)"
                    )
                    cvss_pr = gr.Radio(
                        choices=["None (N)", "Low (L)", "High (H)"],
                        value="None (N)",
                        label="Privileges Required (PR)"
                    )
                    cvss_ui = gr.Radio(
                        choices=["None (N)", "Required (R)"],
                        value="None (N)",
                        label="User Interaction (UI)"
                    )
                    cvss_s = gr.Radio(
                        choices=["Unchanged (U)", "Changed (C)"],
                        value="Unchanged (U)",
                        label="Scope (S)"
                    )

                with gr.Column(scale=6):
                    gr.Markdown("#### 💥 Impact Metrics (CIA Triad)")
                    cvss_c = gr.Radio(
                        choices=["High (H)", "Low (L)", "None (N)"],
                        value="High (H)",
                        label="Confidentiality Impact (C)"
                    )
                    cvss_i = gr.Radio(
                        choices=["High (H)", "Low (L)", "None (N)"],
                        value="High (H)",
                        label="Integrity Impact (I)"
                    )
                    cvss_a = gr.Radio(
                        choices=["High (H)", "Low (L)", "None (N)"],
                        value="High (H)",
                        label="Availability Impact (A)"
                    )
                    
                    cvss_calc_btn = gr.Button("⚡ Calculate CVSS v3.1 Base Score", variant="primary")

                    cvss_result_md = gr.Markdown(
                        value=calculate_cvss_ui("Network (N)", "Low (L)", "None (N)", "None (N)", "Unchanged (U)", "High (H)", "High (H)", "High (H)"),
                        elem_classes=["metric-box"]
                    )

            # Auto calculate on metric change
            metric_inputs = [cvss_av, cvss_ac, cvss_pr, cvss_ui, cvss_s, cvss_c, cvss_i, cvss_a]
            for comp in metric_inputs:
                comp.change(calculate_cvss_ui, inputs=metric_inputs, outputs=[cvss_result_md])
            cvss_calc_btn.click(calculate_cvss_ui, inputs=metric_inputs, outputs=[cvss_result_md])

        # -------------------------------------------------------------
        # Tab 5: Architecture & ReAct Paradigm
        # -------------------------------------------------------------
        with gr.Tab("📖 Architecture & ReAct Flow", id="tab_arch"):
            gr.Markdown("""
            ### 🏗️ VulnGuard-ReAct Architecture & Multi-Tool Orchestration

            This application implements an autonomous **ReAct (Reasoning + Acting)** agent framework for cybersecurity vulnerability intelligence and remediation.

            ```
                                    ┌────────────────────────┐
                                    │   User Security Query  │
                                    └───────────┬────────────┘
                                                │
                                                ▼
                                    ┌────────────────────────┐
                        ┌──────────►│   ReAct Agent Core     │◄─────────┐
                        │           │   (LangChain / DeepSeek)│          │
                        │           └───────────┬────────────┘          │
                        │                       │                       │
               [Observe Tool Output]   [Reasoning / Thought Loop]       │
                        │                       │                       │
                        │                       ▼                       │
                        │           ┌────────────────────────┐          │
                        │           │   Autonomous Tool Call  │──────────┘
                        │           └───────────┬────────────┘
                        │                       │
                        ├───────────────────────┴───────────────────────┐
                        ▼                                               ▼
            ┌───────────────────────────┐                   ┌───────────────────────────┐
            │       REAL FREE APIS      │                   │     ALGORITHMIC & SAST    │
            ├───────────────────────────┤                   ├───────────────────────────┤
            │ • OSV.dev Database API    │                   │ • Official FIRST CVSS v3.1│
            │ • CISA KEV Live Feed      │                   │ • SAST Code Security SAST │
            │ • Serper Threat Search    │                   │ • Defensive Patch Gen     │
            │ • Package Dependency Audit│                   │ • Threat Telemetry Sim    │
            └───────────────────────────┘                   └───────────────────────────┘
                                                │
                                                ▼
                                    ┌────────────────────────┐
                                    │ Final Synthesized Triage│
                                    │    Executive Report    │
                                    └────────────────────────┘
            ```

            #### Key Capabilities:
            1. **Autonomous ReAct Loop**: The agent determines whether to query OSV for affected package ranges, check CISA KEV for active exploitation, calculate exact CVSS impact scores, search live vendor bulletins, or inspect code for CWEs.
            2. **Real-World API Grounding**: Integrates live endpoints from OSV.dev and CISA without requiring proprietary paid licenses.
            3. **Defensive Alignment**: Strictly engineered for cyber defense, patch verification, vulnerability remediation, and enterprise risk reduction.
            """)

# Vercel entrypoint (pyproject.toml -> [tool.vercel] entrypoint = "app:app").
# Gradio is mounted at "/" on a FastAPI app; the ASGI app is named `app`.
app = gr.mount_gradio_app(FastAPI(), demo, path="/")

if __name__ == "__main__":
    demo.launch()
