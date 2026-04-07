"""
06: The Business Operations Agent
=================================

Build an agent that handles real-world business tasks using HiveAgent MCP — 
743 tools across 36 industry verticals, from insurance claims to construction 
permits to international trade.

This example shows how to connect the Claude Agent SDK to a production MCP 
server and execute multi-step business workflows with a single agent.

Requirements:
    pip install anthropic hiveagent-mcp

No API keys needed for HiveAgent — the MCP endpoint is open.
"""

import anthropic
import httpx
import json

# ============================================================================
# HiveAgent MCP Client — connects to 743 tools via JSON-RPC 2.0
# ============================================================================

HIVEAGENT_MCP = "https://hiveagentiq.com/mcp"

def mcp_call(method: str, params: dict = None) -> dict:
    """Make a JSON-RPC 2.0 call to HiveAgent MCP."""
    response = httpx.post(
        HIVEAGENT_MCP,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
        timeout=30,
    )
    result = response.json()
    if "error" in result:
        raise Exception(f"MCP error: {result['error']['message']}")
    return result.get("result", {})


def call_tool(name: str, arguments: dict = None) -> dict:
    """Call a specific HiveAgent tool."""
    result = mcp_call("tools/call", {"name": name, "arguments": arguments or {}})
    # Parse the text content from MCP response envelope
    if "content" in result and result["content"]:
        text = result["content"][0].get("text", "{}")
        return json.loads(text) if text.startswith("{") or text.startswith("[") else text
    return result


# ============================================================================
# Example 1: Discover what's available
# ============================================================================

def discover_tools():
    """Use the discovery meta-tool to find relevant tools by natural language."""
    
    print("=" * 60)
    print("DISCOVERY: What tools are available for insurance?")
    print("=" * 60)
    
    result = call_tool("hiveagent_discover", {"query": "process insurance claims"})
    
    print(f"\nFound {len(result.get('matches', []))} matching tools:")
    for match in result.get("matches", [])[:5]:
        print(f"  → {match['tool_name']} ({match['vertical']})")
        print(f"    {match.get('description', '')[:80]}...")
    
    return result


# ============================================================================
# Example 2: Process a full insurance claim (composite workflow)
# ============================================================================

def process_insurance_claim():
    """
    One call replaces 4 separate tool calls:
    intake → damage assessment → subrogation check → adjuster report
    """
    
    print("\n" + "=" * 60)
    print("WORKFLOW: Full Insurance Claim Processing")
    print("=" * 60)
    
    result = call_tool("workflow_full_insurance_claim", {
        "claim_type": "auto",
        "policy_number": "POL-2026-87432",
        "incident_details": "Rear-end collision at intersection of 5th and Main. "
                           "Other driver ran red light. Police report #2026-4521.",
        "evidence": "Dashboard camera footage, 3 photos of vehicle damage, "
                   "police report, witness statement from passenger."
    })
    
    print(f"\nClaim ID: {result.get('claim_intake', {}).get('claim_id', 'N/A')}")
    print(f"Status: {result.get('claim_intake', {}).get('status', 'N/A')}")
    
    damage = result.get("damage_assessment", {})
    if isinstance(damage, dict):
        est = damage.get("estimated_damage_range", damage.get("estimated_range", {}))
        if isinstance(est, dict):
            print(f"Estimated damage: ${est.get('low', '?')} - ${est.get('high', '?')}")
    
    print(f"Total cost: ${result.get('total_cost_usd', 'N/A')}")
    print(f"Summary: {result.get('summary', 'N/A')}")
    
    return result


# ============================================================================
# Example 3: Construction project setup
# ============================================================================

def setup_construction_project():
    """Look up zoning, then check permit requirements."""
    
    print("\n" + "=" * 60)
    print("CONSTRUCTION: Zoning + Permit Lookup")
    print("=" * 60)
    
    # Step 1: Check zoning
    zoning = call_tool("construction_lookup_zoning", {
        "address": "742 Evergreen Terrace",
        "municipality": "Austin",
        "proposed_use": "residential_addition"
    })
    print(f"\nZoning: {zoning.get('zone_code', 'N/A')} - {zoning.get('zone_name', 'N/A')}")
    
    # Step 2: Check permits needed
    permits = call_tool("trades_lookup_permits", {
        "municipality": "Austin",
        "trade_type": "general_construction",
        "job_description": "2000 sqft residential addition with new electrical and plumbing"
    })
    print(f"Permits required: {len(permits.get('permits_required', []))}")
    for p in permits.get("permits_required", [])[:3]:
        if isinstance(p, dict):
            print(f"  → {p.get('name', p.get('permit_type', 'Unknown'))}")
        else:
            print(f"  → {p}")
    
    return {"zoning": zoning, "permits": permits}


# ============================================================================
# Example 4: International trade compliance
# ============================================================================

def check_trade_compliance():
    """Classify an HS code and screen sanctions — two critical steps for any import."""
    
    print("\n" + "=" * 60)
    print("TRADE: HS Classification + Sanctions Screening")
    print("=" * 60)
    
    # Step 1: Classify the product
    hs = call_tool("trade_classify_hs", {
        "product_description": "Industrial-grade lithium-ion battery cells, 3.7V, 5000mAh",
        "origin_country": "CN",
        "destination_country": "US"
    })
    print(f"\nHS Code: {hs.get('hs_code', 'N/A')}")
    print(f"Duty Rate: {hs.get('duty_rate_pct', 'N/A')}%")
    
    # Step 2: Screen the supplier
    sanctions = call_tool("trade_screen_sanctions", {
        "entity_name": "Shenzhen Battery Technology Co Ltd",
        "entity_type": "company",
        "countries": ["CN"]
    })
    print(f"Sanctions clear: {sanctions.get('clear', 'N/A')}")
    print(f"Risk level: {sanctions.get('risk_level', 'N/A')}")
    
    return {"hs_classification": hs, "sanctions": sanctions}


# ============================================================================
# Example 5: Using the intent router
# ============================================================================

def route_an_intent():
    """Let HiveAgent figure out which tools to use based on natural language."""
    
    print("\n" + "=" * 60)
    print("INTENT ROUTER: Natural language → execution plan")
    print("=" * 60)
    
    result = call_tool("intent_route", {
        "intent": "I need to hire a software engineer. Screen 3 resumes, "
                 "check market compensation for senior engineers in Austin, "
                 "and generate interview questions.",
        "context": {"industry": "technology", "location": "Austin, TX"},
        "budget": 10.0,
        "urgency": "normal"
    })
    
    plan = result.get("plan", {})
    print(f"\nStrategy: {plan.get('strategy', 'N/A')}")
    print(f"Estimated cost: ${plan.get('estimated_cost', 'N/A')}")
    print(f"Tools to use:")
    for tool in plan.get("tools", [])[:5]:
        if isinstance(tool, dict):
            print(f"  → {tool.get('tool_name', tool.get('name', 'Unknown'))}")
        else:
            print(f"  → {tool}")
    
    return result


# ============================================================================
# Run all examples
# ============================================================================

if __name__ == "__main__":
    print("\n🐝 HiveAgent Business Operations Agent")
    print("=" * 60)
    print(f"Endpoint: {HIVEAGENT_MCP}")
    
    # Check connection
    tools_result = mcp_call("tools/list")
    tool_count = len(tools_result.get("tools", []))
    print(f"Connected: {tool_count} tools available\n")
    
    # Run examples
    discover_tools()
    process_insurance_claim()
    setup_construction_project()
    check_trade_compliance()
    route_an_intent()
    
    print("\n" + "=" * 60)
    print("✓ All examples complete")
    print(f"\nLearn more: https://hiveagentiq.com/docs")
    print(f"Try live: https://hiveagentiq.com/playground.html")
    print(f"Install: pip install hiveagent-mcp")
    print("=" * 60)
