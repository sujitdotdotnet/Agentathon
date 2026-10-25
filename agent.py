"""
VulnGuard Agent Module
Constructs the autonomous ReAct Cybersecurity Vulnerability Agent using LangChain's create_agent.
Provides trace capture for real-time observation of the ReAct thought loop.
"""

import os
import json
from typing import Dict, Any, List, Generator, Tuple
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from tools import (
    lookup_cve,
    check_cisa_kev,
    audit_package_dependency,
    search_live_threat_intel,
    calculate_cvss_score,
    analyze_code_vulnerabilities,
    generate_remediation_patch,
    simulate_threat_intel_feed,
)

load_dotenv()

SYSTEM_PROMPT = """You are VulnGuard-ReAct, an elite autonomous Cybersecurity Vulnerability Researcher and Incident Triage Copilot.

Your primary mission is DEFENSIVE vulnerability intelligence, threat modeling, code security auditing, and remediation engineering.

You strictly operate within the ReAct (Reasoning + Acting) loop:
1. **Reason (Thought)**: Before acting, always explain your reasoning. State what information is missing, what hypothesis you are testing, and why you are calling a specific tool.
2. **Act (Tool Execution)**: Call the appropriate tool from your toolset:
   - `lookup_cve`: Use for CVE/GHSA queries to fetch authoritative OSV/NVD records, CVSS scores, and affected versions.
   - `check_cisa_kev`: Use to verify if a vulnerability is on the official CISA Known Exploited Vulnerabilities catalog (in-the-wild exploitation / ransomware use).
   - `audit_package_dependency`: Use to check specific library packages (PyPI, npm, Maven, Go, etc.) and versions for known advisories.
   - `search_live_threat_intel`: Use for breaking zero-day news, vendor security bulletins, proof-of-concept mitigations, or threat actor campaigns.
   - `calculate_cvss_score`: Use to compute mathematically precise CVSS v3.1 base score, vector strings, and severity ratings.
   - `analyze_code_vulnerabilities`: Use to perform deep static analysis (SAST) on provided code snippets for CWEs and security flaws.
   - `generate_remediation_patch`: Use to craft production-grade secure code patches, input validation, and defensive hardening.
   - `simulate_threat_intel_feed`: Use when asked for simulated threat telemetry, tabletop scenarios, or red-team hypothetical drills.
3. **Observe (Observation)**: Carefully review the tool output. If more investigation is warranted (e.g. you checked a CVE, now check CISA KEV and vendor mitigation advice), proceed to the next tool.
4. **Synthesize**: Present a structured, authoritative, actionable defensive report:
   - **Executive Summary & Severity**: High-level risk assessment for leadership.
   - **Technical Root Cause**: Underlying weakness (CWE, protocol, logic).
   - **Exploitability & Threat Actor Telemetry**: CISA KEV status, known active exploitation, ransomware linkages.
   - **CVSS Scoring & Impact**: Base score, vector, and blast radius (CIA triad).
   - **Remediation & Hardening Plan**: Immediate workarounds, safe upgrade versions, code patch diffs, and validation tests.

DEFENSIVE SAFETY MANDATE:
- Never provide weaponized exploit payloads or instructions on how to attack targets.
- Always guide users toward defense-in-depth, patching, mitigation, and secure design.
"""

def build_agent():
    """Initializes and returns the compiled ReAct agent graph."""
    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0.1,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )

    tools = [
        lookup_cve,
        check_cisa_kev,
        audit_package_dependency,
        search_live_threat_intel,
        calculate_cvss_score,
        analyze_code_vulnerabilities,
        generate_remediation_patch,
        simulate_threat_intel_feed,
    ]

    agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent_graph


# Singleton agent instance
_agent_instance = None

def get_agent():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = build_agent()
    return _agent_instance


def run_agent_streaming(user_query: str, chat_history: List[Dict[str, str]] = None) -> Generator[Tuple[str, str], None, None]:
    """
    Streams the ReAct agent's execution.
    Yields (current_trace_markdown, current_agent_response).
    """
    agent = get_agent()
    
    # Prepare message history
    messages = []
    if chat_history:
        for turn in chat_history:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    
    messages.append(HumanMessage(content=user_query))

    trace_steps = []
    step_counter = 1
    final_response = ""

    yield ("*Initializing ReAct Agent... Analyzing query and formulating plan...*", "")

    try:
        inputs = {"messages": messages}
        for update in agent.stream(inputs, stream_mode="updates"):
            for node, data in update.items():
                if node == "model":
                    for msg in data.get("messages", []):
                        if isinstance(msg, AIMessage):
                            content = msg.content or ""
                            tool_calls = getattr(msg, "tool_calls", [])
                            
                            if tool_calls:
                                # This is a ReAct reasoning step with tool calls
                                thought_snippet = content.strip() if content else "Evaluating parameters and selecting appropriate security tool..."
                                trace_entry = (
                                    f"### 🧠 Step {step_counter}: Agent Reasoning & Tool Selection\n"
                                    f"> **Thought:** {thought_snippet}\n\n"
                                )
                                for tc in tool_calls:
                                    tool_name = tc.get("name", "tool")
                                    args = tc.get("args", {})
                                    args_str = json.dumps(args, indent=2)
                                    trace_entry += (
                                        f"- 🛠️ **Calling Tool:** `{tool_name}`\n"
                                        f"```json\n{args_str}\n```\n"
                                    )
                                trace_steps.append(trace_entry)
                                step_counter += 1
                                current_trace = "\n\n---\n\n".join(trace_steps)
                                yield (current_trace, "*Agent is executing tools and gathering telemetry...*")
                            else:
                                # Final synthesis
                                final_response = content
                                trace_steps.append(
                                    f"### 🎯 Step {step_counter}: Final Synthesis & Security Assessment\n"
                                    f"> **Conclusion:** Intelligence gathered across all tools. Generating structured defensive vulnerability report."
                                )
                                current_trace = "\n\n---\n\n".join(trace_steps)
                                yield (current_trace, final_response)

                elif node == "tools":
                    # Tool execution observations
                    for msg in data.get("messages", []):
                        if isinstance(msg, ToolMessage):
                            tool_name = msg.name or "Tool"
                            tool_out = msg.content or "No output returned"
                            # Truncate very long outputs for the trace view
                            display_out = tool_out if len(tool_out) <= 1200 else tool_out[:1200] + "\n... [Observation truncated for display]"
                            trace_entry = (
                                f"#### 📥 Observation from `{tool_name}`\n"
                                f"```markdown\n{display_out}\n```\n"
                            )
                            trace_steps.append(trace_entry)
                            current_trace = "\n\n---\n\n".join(trace_steps)
                            yield (current_trace, "*Analyzing tool observation and determining next steps...*")

        if not final_response:
            final_response = "Triage completed, but no direct textual synthesis was generated."
            yield ("\n\n---\n\n".join(trace_steps), final_response)

    except Exception as e:
        err_msg = f"⚠️ Agent Execution Error: {str(e)}"
        trace_steps.append(f"**Error Encountered:** {err_msg}")
        yield ("\n\n---\n\n".join(trace_steps), f"An error occurred while executing the agent: {str(e)}")

