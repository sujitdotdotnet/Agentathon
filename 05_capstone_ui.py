"""
05 - Capstone: Enterprise Incident Response Copilot

A production-grade Enterprise Agent that unifies every concept from Mission 2:
- System time & exact business SLA calculations (exact arithmetic)
- Live external vendor status verification (Web API search)
- LLM-powered incident triage (LLM-as-a-Tool)
- On-call escalation & Runbook SOP retrieval (Action & Knowledge tools)
- LangChain ReAct loop (create_agent) with real-time THINK/ACT/OBSERVE trace
- Gradio Operations Dashboard for incident responders

Run: uv run 05_capstone_ui.py, then open the http://127.0.0.1:7860 link.
"""

import os
import json
import urllib.request
from datetime import datetime
from dotenv import load_dotenv
import gradio as gr
from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
if api_key == "" or api_key == "your_deepseek_api_key_here":
    print("No API key found. Please add DEEPSEEK_API_KEY to .env first.")
    exit()

# ====================================================================
# 1. LLM as a Tool: Incident Triage (Language Task)
# ====================================================================
triage_llm = ChatDeepSeek(model="deepseek-chat", temperature=0.0)


@tool
def triage_incident(raw_alert: str) -> str:
    """Analyze a raw production alert or incident description using an LLM.
    Returns structured severity (P1=Critical Outage, P2=Degraded Performance,
    P3=Minor Issue), impacted system, root cause hypothesis, and executive summary."""
    prompt = (
        "You are a Site Reliability Engineering (SRE) triage engine. "
        "Analyze the following incident report and output EXACTLY in this format on one line:\n"
        "severity=<P1|P2|P3>; service=<service name>; category=<Database|Network|Payment|API|Compute>; summary=<one crisp line>\n\n"
        "Incident alert: " + raw_alert
    )
    return triage_llm.invoke(prompt).content.strip()


# ====================================================================
# 2. Action Dispatch: On-Call Paging
# ====================================================================
@tool
def page_oncall_team(severity: str, team: str = "SRE") -> str:
    """Page the designated engineering on-call responders based on incident severity (P1, P2, or P3)."""
    sev = severity.upper()
    if "P1" in sev:
        return f"ESCALATED (P1): Paged {team} Primary, SRE Lead, and VP of Engineering. Emergency War Room bridge opened."
    if "P2" in sev:
        return f"DISPATCHED (P2): Paged {team} on-call engineer via PagerDuty. Acknowledgment window: 15 mins."
    return f"LOGGED (P3): Created Jira ticket in {team} backlog for next business day review. No pager alert raised."


# ====================================================================
# 3. Knowledge Tool: Operational Runbook Search
# ====================================================================
RUNBOOKS = {
    "database": (
        "Runbook [DB-01]: High Database Latency / Pool Exhaustion\n"
        "1. Check pg_stat_activity for long-running blocking queries.\n"
        "2. Terminate idle-in-transaction connections older than 5 minutes.\n"
        "3. If connection pool is exhausted, temporarily increase max connections by 25% or scale read replicas.\n"
        "4. Escalate to DBA team if replication lag exceeds 60 seconds."
    ),
    "payment": (
        "Runbook [PAY-02]: Payment Gateway 502 / Checkout Failures\n"
        "1. Verify upstream payment provider status via vendor status tool.\n"
        "2. If provider is degraded, toggle feature flag 'ENABLE_SECONDARY_GATEWAY' to reroute traffic.\n"
        "3. Flush cached auth tokens and verify SSL certificates on the payment proxy.\n"
        "4. Notify customer support team with estimated resolution window."
    ),
    "api": (
        "Runbook [API-03]: High HTTP 5xx Error Spike\n"
        "1. Inspect ingress gateway logs for failing route patterns and status codes.\n"
        "2. Check if recent deployment occurred in the last 60 minutes; execute canary rollback if needed.\n"
        "3. Verify pod memory limits to ensure pods are not crash-looping due to OOMKilled."
    ),
}


@tool
def search_runbooks(topic: str) -> str:
    """Retrieve operational recovery procedures (runbooks) for a system component (database, payment, or api)."""
    query = topic.lower()
    for key, runbook in RUNBOOKS.items():
        if key in query:
            return runbook
    return (
        f"Standard SOP: 1. Isolate failing node. 2. Capture stack traces and heap dump. "
        f"3. Roll back last release if within 1 hour. 4. Escalate to primary on-call."
    )


# ====================================================================
# 4. Deterministic Business Tool: SLA Penalty Calculation (Exact Maths)
# ====================================================================
@tool
def calculate_sla_penalty(downtime_minutes: int, customer_tier: str = "enterprise") -> str:
    """Calculate the contractual SLA breach penalty credit exactly based on downtime duration and customer tier."""
    tier = customer_tier.lower()
    if "enterprise" in tier:
        grace_period = 15
        penalty_per_min = 5000.0  # Rs 5,000 / min
        sla_target = "99.95%"
    elif "business" in tier:
        grace_period = 30
        penalty_per_min = 2000.0  # Rs 2,000 / min
        sla_target = "99.9%"
    else:
        grace_period = 60
        penalty_per_min = 500.0   # Rs 500 / min
        sla_target = "99.5%"

    chargeable_minutes = max(0, downtime_minutes - grace_period)
    total_penalty = chargeable_minutes * penalty_per_min

    return (
        f"SLA Target: {sla_target} | Customer Tier: {tier.title()} | "
        f"Downtime: {downtime_minutes} min (Grace: {grace_period} min) | "
        f"Billable Outage: {chargeable_minutes} min | "
        f"Contractual Credit Penalty: Rs {total_penalty:,.2f}"
    )


# ====================================================================
# 5. External Web Search Tool: Upstream Vendor Outage Check
# ====================================================================
@tool
def check_upstream_vendor_status(vendor_or_service: str) -> str:
    """Search live web advisories to check if an external cloud vendor or SaaS provider (AWS, OpenAI, Stripe, Cloudflare) has an ongoing outage."""
    serper_key = os.getenv("SERPER_API_KEY", "").strip()
    if serper_key == "" or serper_key == "your_serper_api_key_here":
        return (
            "Web search is not configured (SERPER_API_KEY missing in .env). "
            "Proceed with internal diagnostics and runbook procedures."
        )

    query = f"{vendor_or_service} service outage status today"
    try:
        request = urllib.request.Request(
            "https://google.serper.dev/search",
            data=json.dumps({"q": query}).encode("utf-8"),
            headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
            method="POST",
        )
        data = json.loads(urllib.request.urlopen(request, timeout=8).read())
        results = data.get("organic", [])
        if not results:
            return f"No reported outage detected for {vendor_or_service}."
        lines = []
        for item in results[:3]:
            lines.append("- " + str(item.get("title")) + ": " + str(item.get("snippet")))
        return "\n".join(lines)
    except Exception as err:
        return f"Vendor status check failed: {err}"


# ====================================================================
# 6. System Clock Tool: Incident Audit Timestamp
# ====================================================================
@tool
def get_incident_timestamp() -> str:
    """Return the current system time and UTC timestamp for the incident timeline and audit logs."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S (Local System Time)")


# ====================================================================
# Agent Assembly
# ====================================================================
agent = create_agent(
    model="deepseek:deepseek-chat",
    tools=[
        triage_incident,
        page_oncall_team,
        search_runbooks,
        calculate_sla_penalty,
        check_upstream_vendor_status,
        get_incident_timestamp,
    ],
    system_prompt=(
        "You are an expert Enterprise Incident Commander and Site Reliability Copilot. "
        "Your duty is to manage production alerts with precision.\n"
        "Guidelines:\n"
        "1. For incident alerts: Always first run triage_incident, log the current timestamp with get_incident_timestamp, "
        "page the appropriate team via page_oncall_team, and pull relevant mitigation steps via search_runbooks.\n"
        "2. If an alert suspects external vendor failures, verify with check_upstream_vendor_status.\n"
        "3. For SLA calculations: Never guess dollar amounts; always use calculate_sla_penalty.\n"
        "4. Summarize your final assessment professionally with severity, actions taken, and recommended next steps."
    ),
)


# ====================================================================
# Gradio UI
# ====================================================================
def handle_incident(prompt: str):
    if not prompt.strip():
        return "Please input an incident alert or enterprise request.", ""

    result = agent.invoke({"messages": [HumanMessage(content=prompt)]})

    trace = ""
    answer = "(No response generated)"
    for message in result["messages"]:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                trace += f"**THINK / ACT** - Invoke `{call['name']}` with:\n```json\n{json.dumps(call['args'], indent=2)}\n```\n\n"
        elif isinstance(message, ToolMessage):
            trace += f"**OBSERVE** -> Output:\n```text\n{message.content}\n```\n\n"
        elif isinstance(message, AIMessage) and message.content:
            answer = message.content

    if not trace:
        trace = "_Direct model answer (no tools required)._"

    return answer, trace


enterprise_examples = [
    ["CRITICAL OUTAGE: All checkout transactions are failing with HTTP 502 errors. Customers cannot complete orders."],
    ["High latency alert: Postgres primary cluster connection pool is 98% full and queries are timing out. Retrieve runbook."],
    ["Our external microservices are failing to connect to OpenAI API endpoints. Check if OpenAI has an ongoing outage."],
    ["The core billing API suffered 48 minutes of downtime. Calculate our contractual SLA penalty for an Enterprise customer."],
]

with gr.Blocks(title="Enterprise Incident Copilot") as demo:
    gr.Markdown(
        "# Enterprise Incident Response Copilot\n"
        "Production AI Operations Agent equipped with **LLM Incident Triage**, **On-Call Escalations**, "
        "**Runbook Retrieval**, **External Vendor Outage Verification**, and **Contractual SLA Calculators**."
    )

    with gr.Row():
        with gr.Column(scale=3):
            input_box = gr.Textbox(
                label="Incident Alert / Operational Command",
                placeholder="Paste a production incident alert or query...",
                lines=3,
            )
            with gr.Row():
                submit_btn = gr.Button("Execute Incident Response", variant="primary")
                clear_btn = gr.Button("Clear")

        with gr.Column(scale=2):
            gr.Examples(
                examples=enterprise_examples,
                inputs=input_box,
                label="Enterprise Production Scenarios",
            )

    with gr.Row():
        with gr.Column(scale=1):
            answer_box = gr.Markdown(label="Incident Commander Briefing")
        with gr.Column(scale=1):
            trace_box = gr.Markdown("Live Agent Execution Trace (THINK / ACT / OBSERVE) will stream here...")

    submit_btn.click(handle_incident, input_box, [answer_box, trace_box])
    input_box.submit(handle_incident, input_box, [answer_box, trace_box])
    clear_btn.click(lambda: ("", "", ""), outputs=[input_box, answer_box, trace_box])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, theme=gr.themes.Soft())
