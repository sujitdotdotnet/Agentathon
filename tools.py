"""
VulnGuard Tools Module
Provides real free cybersecurity APIs, algorithmic scoring, and LLM-powered mock/simulation tools.
"""

import os
import json
import math
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek

load_dotenv()

# Global memory cache for CISA KEV to avoid repeated large network downloads
_CISA_KEV_CACHE: Optional[List[Dict[str, Any]]] = None

def get_llm():
    """Helper to initialize LLM for LLM-powered tools."""
    return ChatDeepSeek(model="deepseek-chat", temperature=0.1)


# -------------------------------------------------------------------------
# Tool 1: Real API - OSV.dev Free Vulnerability Database Lookup
# -------------------------------------------------------------------------
@tool
def lookup_cve(cve_id: str) -> str:
    """
    Look up detailed vulnerability intelligence for a CVE ID (e.g. 'CVE-2024-3094', 'CVE-2021-44228') 
    using the official open-access OSV.dev database and NIST NVD public feeds.
    Returns CVSS score, severity tier, affected packages/versions, CWE IDs, and remediation links.
    """
    clean_id = cve_id.strip().upper()
    if not clean_id.startswith("CVE-") and not clean_id.startswith("GHSA-"):
        # Auto-prefix if user just gave numbers like 2024-3094
        if "-" in clean_id:
            clean_id = f"CVE-{clean_id}"

    try:
        url = f"https://api.osv.dev/v1/vulns/{clean_id}"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            vuln_id = data.get("id", clean_id)
            summary = data.get("summary", "No summary provided")
            details = data.get("details", "")[:800]
            if len(data.get("details", "")) > 800:
                details += "... [truncated]"

            severity_entries = data.get("severity", [])
            cvss_vector = "Not specified"
            for s in severity_entries:
                if "score" in s:
                    cvss_vector = f"{s.get('type')}: {s.get('score')}"

            affected_info = []
            for aff in data.get("affected", [])[:5]:
                pkg = aff.get("package", {})
                pkg_name = pkg.get("name", "Unknown Package")
                ecosystem = pkg.get("ecosystem", "Generic")
                ranges = aff.get("ranges", [])
                fixed_versions = []
                for r in ranges:
                    for ev in r.get("events", []):
                        if "fixed" in ev:
                            fixed_versions.append(ev["fixed"])
                aff_str = f"Package: {pkg_name} ({ecosystem})"
                if fixed_versions:
                    aff_str += f" | Fixed in: {', '.join(fixed_versions)}"
                affected_info.append(aff_str)

            refs = [ref.get("url", "") for ref in data.get("references", [])[:4] if ref.get("url")]

            return (
                f"### [OSV Intelligence Record: {vuln_id}]\n"
                f"- **Summary:** {summary}\n"
                f"- **CVSS Vector/Score:** {cvss_vector}\n"
                f"- **Affected Packages:**\n  " + ("\n  ".join(affected_info) if affected_info else "See details") + "\n"
                f"- **Overview Details:**\n{details}\n"
                f"- **Advisory References:**\n  " + "\n  ".join([f"- {u}" for u in refs])
            )
        elif resp.status_code == 404:
            return (
                f"Notice: OSV database has no direct record for {clean_id}. "
                f"Recommend checking NIST NVD or executing live_threat_intel_search tool for this CVE."
            )
        else:
            return f"OSV API returned status code {resp.status_code} for {clean_id}."
    except Exception as e:
        return f"Error connecting to OSV database: {str(e)}. Fallback to threat search."


# -------------------------------------------------------------------------
# Tool 2: Real API - CISA Known Exploited Vulnerabilities (KEV) Catalog
# -------------------------------------------------------------------------
@tool
def check_cisa_kev(cve_id: str) -> str:
    """
    Check if a CVE is listed on the official US Cybersecurity and Infrastructure Security Agency (CISA)
    Known Exploited Vulnerabilities (KEV) catalog.
    This reveals whether attackers are actively exploiting it in the wild, whether it is used in ransomware campaigns,
    and mandatory federal remediation deadlines.
    """
    global _CISA_KEV_CACHE
    clean_id = cve_id.strip().upper()
    if not clean_id.startswith("CVE-") and "-" in clean_id:
        clean_id = f"CVE-{clean_id}"

    try:
        if _CISA_KEV_CACHE is None:
            url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                _CISA_KEV_CACHE = resp.json().get("vulnerabilities", [])
            else:
                return f"Could not retrieve CISA KEV catalog (HTTP {resp.status_code})."

        match = next((item for item in _CISA_KEV_CACHE if item.get("cveID", "").upper() == clean_id), None)
        if match:
            return (
                f"### 🚨 CISA KEV CRITICAL ALERT: {clean_id} IS ACTIVELY EXPLOITED IN THE WILD!\n"
                f"- **Product / Vendor:** {match.get('vendorProject')} {match.get('product')}\n"
                f"- **Vulnerability Name:** {match.get('vulnerabilityName')}\n"
                f"- **Date Added to KEV:** {match.get('dateAdded')}\n"
                f"- **Known Ransomware Campaign Use:** {match.get('knownRansomwareCampaignUse', 'Unknown')}\n"
                f"- **CISA Required Remediation Action:** {match.get('requiredAction')}\n"
                f"- **Federal Due Date:** {match.get('dueDate')}\n"
                f"- **Associated CWEs:** {', '.join(match.get('cwes', []))}\n"
                f"- **CISA Notes:** {match.get('notes')}"
            )
        else:
            return (
                f"### ✅ CISA KEV Status for {clean_id}:\n"
                f"Not currently listed in CISA's Known Exploited Vulnerabilities catalog. "
                f"This means there is no widespread confirmed active weaponized campaign tracked in the federal catalog, "
                f"though security hygiene and patching remain recommended."
            )
    except Exception as e:
        return f"Error querying CISA KEV catalog: {str(e)}"


# -------------------------------------------------------------------------
# Tool 3: Real API - OSV Package & Dependency Vulnerability Audit
# -------------------------------------------------------------------------
@tool
def audit_package_dependency(package_name: str, ecosystem: str, version: str) -> str:
    """
    Audit an open-source software dependency package for known vulnerabilities using the OSV.dev API.
    Args:
        package_name: The name of the package (e.g. 'jinja2', 'requests', 'express', 'lodash', 'spring-core').
        ecosystem: The package ecosystem (e.g. 'PyPI', 'npm', 'Maven', 'Go', 'NuGet', 'crates.io').
        version: The exact version installed (e.g. '2.11.2', '4.17.21').
    """
    clean_pkg = package_name.strip()
    clean_eco = ecosystem.strip()
    clean_ver = version.strip()

    payload = {
        "package": {
            "name": clean_pkg,
            "ecosystem": clean_eco
        },
        "version": clean_ver
    }

    try:
        url = "https://api.osv.dev/v1/query"
        resp = requests.post(url, json=payload, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            vulns = data.get("vulns", [])
            if not vulns:
                return f"✅ Clean: No known vulnerabilities found in OSV database for {clean_pkg} v{clean_ver} ({clean_eco})."

            report = [f"⚠️ Found {len(vulns)} vulnerability advisory(ies) affecting {clean_pkg} v{clean_ver} ({clean_eco}):\n"]
            for v in vulns[:6]:
                v_id = v.get("id")
                summary = v.get("summary", "No brief summary available")
                sev = "Unknown severity"
                for s in v.get("severity", []):
                    if "score" in s:
                        sev = f"{s.get('type')}: {s.get('score')}"
                report.append(f"- **{v_id}**: {summary} (Score: {sev})")

            report.append("\nRecommended action: Upgrade to the latest stable release or apply vendor mitigations.")
            return "\n".join(report)
        else:
            return f"OSV query returned HTTP {resp.status_code}."
    except Exception as e:
        return f"Error auditing package dependency: {str(e)}"


# -------------------------------------------------------------------------
# Tool 4: Real API - Live Threat Intelligence & Web Search (Serper)
# -------------------------------------------------------------------------
@tool
def search_live_threat_intel(query: str) -> str:
    """
    Search the live web for the latest threat intelligence, zero-day advisories,
    vendor mitigation bulletins, security researcher analyses, and patch announcements via Google Serper.
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "Serper API key not configured. Fallback to offline knowledge."

    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        # Enrich query with cybersecurity intent
        search_payload = {"q": f"{query} security advisory vulnerability patch", "num": 5}
        resp = requests.post(url, headers=headers, json=search_payload, timeout=8)
        if resp.status_code == 200:
            results = resp.json().get("organic", [])
            if not results:
                return f"No live search results found for query: '{query}'."

            intel_output = [f"### Live Threat Intelligence Search Results for: '{query}'\n"]
            for idx, res in enumerate(results[:4], 1):
                title = res.get("title", "")
                link = res.get("link", "")
                snippet = res.get("snippet", "")
                date = res.get("date", "Recent")
                intel_output.append(f"**[{idx}] {title}** ({date})\n- Link: {link}\n- Brief: {snippet}\n")
            return "\n".join(intel_output)
        else:
            return f"Live search failed with status code {resp.status_code}."
    except Exception as e:
        return f"Error executing threat search: {str(e)}"


# -------------------------------------------------------------------------
# Tool 5: Mathematical Algorithmic Tool - Official CVSS v3.1 Calculator
# -------------------------------------------------------------------------
@tool
def calculate_cvss_score(
    attack_vector: str,
    attack_complexity: str,
    privileges_required: str,
    user_interaction: str,
    scope: str,
    confidentiality: str,
    integrity: str,
    availability: str
) -> str:
    """
    Calculate the official FIRST CVSS v3.1 Base Score, Severity Rating, and Vector String.
    Args:
        attack_vector: 'N' (Network), 'A' (Adjacent), 'L' (Local), 'P' (Physical)
        attack_complexity: 'L' (Low), 'H' (High)
        privileges_required: 'N' (None), 'L' (Low), 'H' (High)
        user_interaction: 'N' (None), 'R' (Required)
        scope: 'U' (Unchanged), 'C' (Changed)
        confidentiality: 'N' (None), 'L' (Low), 'H' (High)
        integrity: 'N' (None), 'L' (Low), 'H' (High)
        availability: 'N' (None), 'L' (Low), 'H' (High)
    """
    av_map = {'N': 0.85, 'A': 0.62, 'L': 0.55, 'P': 0.20}
    ac_map = {'L': 0.77, 'H': 0.44}
    pr_u_map = {'N': 0.85, 'L': 0.62, 'H': 0.27}
    pr_c_map = {'N': 0.85, 'L': 0.68, 'H': 0.50}
    ui_map = {'N': 0.85, 'R': 0.62}
    cia_map = {'N': 0.0, 'L': 0.22, 'H': 0.56}

    try:
        av = attack_vector.upper().strip()
        ac = attack_complexity.upper().strip()
        pr = privileges_required.upper().strip()
        ui = user_interaction.upper().strip()
        s = scope.upper().strip()
        c = confidentiality.upper().strip()
        i = integrity.upper().strip()
        a = availability.upper().strip()

        av_val = av_map.get(av, 0.85)
        ac_val = ac_map.get(ac, 0.77)
        pr_val = (pr_c_map if s == 'C' else pr_u_map).get(pr, 0.85)
        ui_val = ui_map.get(ui, 0.85)
        c_val = cia_map.get(c, 0.56)
        i_val = cia_map.get(i, 0.56)
        a_val = cia_map.get(a, 0.56)

        iss = 1.0 - ((1.0 - c_val) * (1.0 - i_val) * (1.0 - a_val))
        if s == 'U':
            impact = 6.42 * iss
        else:
            impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)

        exploitability = 8.22 * av_val * ac_val * pr_val * ui_val

        if impact <= 0:
            base_score = 0.0
        elif s == 'U':
            base_score = min(round(math.ceil((impact + exploitability) * 10) / 10, 1), 10.0)
        else:
            base_score = min(round(math.ceil(1.08 * (impact + exploitability) * 10) / 10, 1), 10.0)

        # Rating tier
        if base_score == 0.0:
            rating = "None"
        elif 0.1 <= base_score <= 3.9:
            rating = "Low"
        elif 4.0 <= base_score <= 6.9:
            rating = "Medium"
        elif 7.0 <= base_score <= 8.9:
            rating = "High"
        else:
            rating = "Critical"

        vector_str = f"CVSS:3.1/AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{c}/I:{i}/A:{a}"

        return (
            f"### [CVSS v3.1 Calculation Result]\n"
            f"- **Vector String:** `{vector_str}`\n"
            f"- **Base Score:** **{base_score} / 10.0**\n"
            f"- **Severity Tier:** **{rating.upper()}**\n"
            f"- **Impact Score:** {round(impact, 2)} | **Exploitability Score:** {round(exploitability, 2)}\n"
            f"- **Triage Assessment:** {'Immediate emergency patch required (P0).' if rating == 'Critical' else 'Prioritize remediation according to standard SLA.'}"
        )
    except Exception as e:
        return f"Error calculating CVSS score: {str(e)}"


# -------------------------------------------------------------------------
# Tool 6: Mock / LLM Tool - Static Code Vulnerability Analyzer
# -------------------------------------------------------------------------
@tool
def analyze_code_vulnerabilities(code_snippet: str, language: str) -> str:
    """
    Perform deep static application security testing (SAST) on a code snippet.
    Identifies software vulnerabilities (e.g. SQL Injection, Path Traversal, SSRF, Deserialization,
    Buffer Overflows, Insecure Cryptography, Prototype Pollution, Broken Access Control),
    traces taint propagation, assigns CWE identifiers, and details the defensive risk.
    """
    llm = get_llm()
    prompt = f"""
You are an expert Application Security and Static Analysis (SAST) auditor.
Analyze the following {language} code snippet for security vulnerabilities:

```{language}
{code_snippet}
```

Instructions:
1. Identify any vulnerable patterns, insecure functions, or untrusted input flows.
2. Provide the CWE ID (e.g., CWE-89 SQLi, CWE-78 Command Injection, CWE-502 Deserialization).
3. State the precise vulnerable lines and mechanism.
4. Assess the potential impact (Confidentiality, Integrity, Availability).
5. Explain how a defensive engineer can eliminate this vulnerability.
Be concise, accurate, and strictly defensive.
"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error executing static code analysis: {str(e)}"


# -------------------------------------------------------------------------
# Tool 7: Mock / LLM Tool - Defensive Remediation Patch & Hardening Generator
# -------------------------------------------------------------------------
@tool
def generate_remediation_patch(vulnerability_description: str, code_or_config: str, language: str) -> str:
    """
    Generate a production-ready, hardened defensive code patch, secure replacement snippet,
    and mitigation guidance for a diagnosed vulnerability.
    Includes input validation, parameterized queries, safe serialization, or architectural hardening.
    """
    llm = get_llm()
    prompt = f"""
You are a Principal Defensive Security Engineer and Secure Coding specialist.
Generate a secure, hardened patch and remediation guide for the following scenario:

- **Target Language/Config:** {language}
- **Vulnerability Diagnosed:** {vulnerability_description}
- **Original Insecure Code/Config:**
```{language}
{code_or_config}
```

Provide:
1. **Hardened Code Replacement**: Production-grade secure implementation with safe libraries and defenses.
2. **Key Security Controls Applied**: Explain parameterized APIs, sanitization, least-privilege, or defense-in-depth principles.
3. **Verification Test / Assertions**: A brief unit test or check proving the vulnerability is remediated.
Format with clean markdown and code blocks.
"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error generating remediation patch: {str(e)}"


# -------------------------------------------------------------------------
# Tool 8: Mock / LLM Tool - Advanced Threat Telemetry & Zero-Day Simulation
# -------------------------------------------------------------------------
@tool
def simulate_threat_intel_feed(target_technology: str, scenario_type: str) -> str:
    """
    Simulate an advanced proprietary threat intelligence feed (e.g. Mandiant/Recorded Future/CrowdStrike style)
    for hypothetical, emergent zero-day vulnerability scenarios or red-team threat emulation exercises.
    Clearly marks the intelligence as a high-fidelity simulation for security tabletop exercises.
    """
    llm = get_llm()
    prompt = f"""
You are a Senior Threat Intelligence Analyst at a global cyber defense agency.
Generate a realistic simulated threat intelligence advisory for a security tabletop exercise.

- **Target Technology/Ecosystem:** {target_technology}
- **Scenario Focus:** {scenario_type}

Structure the simulated report as follows:
[SIMULATED THREAT INTELLIGENCE ADVISORY - TABLETOP EXERCISE ONLY]
- Threat Actor Attribution (hypothetical APT or cybercrime group)
- Attack Vector & Root Cause Mechanism
- Indicators of Compromise (IoCs - simulated file hashes, network artifacts)
- Detection Signatures (YARA / Sigma / Snort rule concept)
- Immediate Blue Team / Defensive Hardening Recommendations
"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error simulating threat intel feed: {str(e)}"

