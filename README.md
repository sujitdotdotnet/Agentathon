# 🛡️ VulnGuard-ReAct: Autonomous Cybersecurity Vulnerability Intelligence & Remediation Agent

An autonomous **ReAct (Reasoning + Acting)** cybersecurity agent built with **LangChain `create_agent`**, connected to **real open vulnerability APIs**, algorithmic scoring engines, and **LLM-powered simulation tools**, wrapped in a modern **Gradio** web application.

---

## 🌟 Key Highlights & Architecture

### 🧠 The ReAct Cognitive Loop
VulnGuard follows the ReAct paradigm to autonomously investigate vulnerabilities:
1. **Reason (Thought)**: Formulates an investigative hypothesis based on user input.
2. **Act (Tool Execution)**: Autonomously selects and executes specialized cybersecurity tools.
3. **Observe (Observation)**: Ingests structured telemetry from free APIs, live feeds, or static analyzers.
4. **Repeat / Reflect**: Chains multiple tools together (e.g. CVE lookup ➔ CISA KEV check ➔ Live advisory search ➔ Remediation patch).
5. **Synthesize**: Formulates an authoritative defensive triage report.

### 🛠️ Integrated Tool Suite

| Tool | Type | Source / Mechanism | Description |
| :--- | :--- | :--- | :--- |
| `lookup_cve` | **Real Free API** | OSV.dev & NIST NVD | Fetches CVSS scores, affected packages/versions, and advisory links. |
| `check_cisa_kev` | **Real Live Feed** | US CISA Federal Catalog | Checks if a CVE is actively exploited in the wild or used in ransomware attacks. |
| `audit_package_dependency` | **Real Free API** | OSV.dev Ecosystem API | Audits packages (`PyPI`, `npm`, `Maven`, `Go`, etc.) for known advisories and safe upgrade paths. |
| `search_live_threat_intel` | **Real Search API** | Google Serper API | Searches live web for zero-day advisories, vendor bulletins, and security notes. |
| `calculate_cvss_score` | **Mathematical** | FIRST CVSS v3.1 Standard | Computes base score (0.0-10.0), impact, exploitability, and vector string. |
| `analyze_code_vulnerabilities`| **LLM / SAST** | DeepSeek V3 Security Auditor| Performs static analysis, identifies CWEs, and maps taint propagation. |
| `generate_remediation_patch` | **LLM / Patch** | DeepSeek V3 Defensive Eng | Generates production-grade hardened code, sanitization, and unit tests. |
| `simulate_threat_intel_feed` | **LLM / Simulation**| Threat Intel Simulator | Generates simulated dark-web / APT threat advisories for tabletop drills. |

---

## 🖥️ Gradio Application Structure

The Gradio web interface (`http://127.0.0.1:7860`) features 5 dedicated modules:

1. **💬 ReAct Security Copilot**:
   - Interactive conversation with streaming thoughts and responses.
   - **Live ReAct Thought & Tool Execution Trace**: Shows each step's internal thought, exact tool arguments, raw API observations, and synthesis.
   - One-click incident presets (XZ Utils Backdoor, Log4Shell, Dependency Auditing, SQLi, Spring 0-day).

2. **🔍 Code & Dependency Scanner**:
   - Insecure code sandbox with preloaded vulnerability patterns (FastAPI SQLi, Pickle Deserialization, Node Command Injection, SSRF, Prototype Pollution).
   - Generates side-by-side SAST diagnostics and hardened defensive replacement patches.

3. **📡 Live CISA KEV Threat Radar**:
   - Live feed of 1,756+ actively exploited vulnerabilities tracked by CISA.
   - Real-time search and filter by Vendor, CVE ID, or Ransomware Campaign flag.
   - One-click transfer to Agent for instant deep triage.

4. **🧮 CVSS v3.1 Scoring Engine**:
   - Interactive matrix for all 8 base vector metrics (AV, AC, PR, UI, S, C, I, A).
   - Real-time mathematical scoring with dynamic severity badges (Critical, High, Medium, Low).

5. **📖 Architecture & ReAct Flow**:
   - Visual architecture diagram and deep dive into ReAct agent internals and safety guardrails.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Virtual environment (`.venv`) with dependencies installed from `pyproject.toml` / `requirements.txt`.

### 2. Environment Configuration
Ensure your `.env` contains:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
SERPER_API_KEY=your_serper_api_key
```

### 3. Launch the Application
Run:
```bash
.venv\Scripts\python.exe app.py
```
Open your browser at `http://127.0.0.1:7860`.

