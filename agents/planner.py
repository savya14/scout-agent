import time
import json
from google import genai
from dotenv import load_dotenv
import os

from db.queries import search_players, search_player_by_name, find_replacements, get_top_players
from memory.context import build_context_packet, format_context_for_prompt

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ── Tool implementations ──────────────────────────────────────────────────────

def tool_search_players(position=None, max_age=None, min_rating=None, nationality=None, top_n=10):
    results = search_players(position=position, max_age=max_age, min_rating=min_rating, nationality=nationality)
    return {"players": results[:top_n], "count": len(results[:top_n])}


def tool_get_player(name: str):
    player = search_player_by_name(name)
    if not player:
        return {"error": f"Player '{name}' not found."}
    return {"player": player}


def tool_find_replacements(player_name: str, max_age: int = 26):
    player = search_player_by_name(player_name)
    if not player:
        return {"error": f"Player '{player_name}' not found."}
    replacements = find_replacements(
        position=player.get("position", ""),
        current_club=player.get("club_name"),
        max_age=max_age,
        min_rating=max(70, player.get("overall_rating", 80) - 8),
        reference_rating=player.get("overall_rating"),
    )
    return {"original_player": player, "replacements": replacements[:10]}


def tool_top_players(limit: int = 10):
    players = get_top_players(limit)
    return {"players": players}


TOOLS = {
    "search_players": tool_search_players,
    "get_player": tool_get_player,
    "find_replacements": tool_find_replacements,
    "top_players": tool_top_players,
}

TOOL_DESCRIPTIONS = """
Available tools:
1. search_players(position, max_age, min_rating, nationality, top_n) - Search players by filters
2. get_player(name) - Look up a specific player by name
3. find_replacements(player_name, max_age) - Find replacement candidates for a player
4. top_players(limit) - Get the highest rated players overall
"""


# ── Planner loop ──────────────────────────────────────────────────────────────

def run_planner(user_query: str, session_id: str = "default", progress_callback=None) -> dict:
    context = build_context_packet(session_id, user_query)
    context_text = format_context_for_prompt(context)

    trace = []
    tool_calls_log = []
    gathered_data = []

    # Step 1: Planning
    plan_prompt = f"""
You are the Planner Agent for Scout Agent, an AI football scouting platform.

User Query: {user_query}

Session Context:
{context_text}

{TOOL_DESCRIPTIONS}

Decide which tools to call and in what order to answer the query.
Respond ONLY with valid JSON like this:
{{
  "plan": [
    {{"tool": "search_players", "args": {{"position": "ST", "max_age": 25, "min_rating": 82}}}},
    {{"tool": "get_player", "args": {{"name": "Haaland"}}}}
  ],
  "reasoning": "One sentence explaining the plan."
}}
Do not include tools not in the list. Max 3 tool calls.
"""
    try:
        plan_response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=plan_prompt,
        )
        plan_text = plan_response.text.strip().replace("```json", "").replace("```", "").strip()
        plan_data = json.loads(plan_text)
        plan = plan_data.get("plan", [])
        reasoning = plan_data.get("reasoning", "")
    except Exception as e:
        plan = []
        reasoning = f"Planning failed: {e}"

    trace.append({"agent": "Planner", "action": "plan", "detail": reasoning})
    if progress_callback:
        progress_callback(f"Plan: {reasoning}", "plan")

    # Step 2: Execute tools
    for step in plan[:3]:
        tool_name = step.get("tool")
        args = step.get("args", {})

        if tool_name not in TOOLS:
            continue

        if progress_callback:
            progress_callback(f"Calling {tool_name}({args})", "tool_call")

        try:
            result = TOOLS[tool_name](**args)
            gathered_data.append({"tool": tool_name, "args": args, "result": result})
            tool_calls_log.append({"tool": tool_name, "args": args})
            trace.append({"agent": "Tool", "action": tool_name, "detail": f"Success — {_summarise(result)}"})
        except Exception as e:
            trace.append({"agent": "Tool", "action": tool_name, "detail": f"Error: {e}"})

        time.sleep(0.3)

    # Step 3: Synthesise
    data_summary = json.dumps(gathered_data, indent=2, default=str)[:6000]

    synthesis_prompt = f"""
You are an elite football scout. Answer the user's query based on the data retrieved.

User Query: {user_query}

Data Retrieved:
{data_summary}

Rules:
- Output plain text only. No markdown, no bullet symbols, no asterisks.
- Be direct and insightful. Sound like a real scout, not a chatbot.
- If players are found, name the top 3 with a brief reason each.
- If no data found, say so honestly.
- Keep response under 300 words.
"""

    if progress_callback:
        progress_callback("Synthesising response...", "synthesis")

    try:
        synthesis_response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=synthesis_prompt,
        )
        final_response = synthesis_response.text.strip()
    except Exception as e:
        final_response = f"Could not generate response: {e}"

    trace.append({"agent": "Synthesiser", "action": "response", "detail": final_response[:100]})

    # Extract players list for frontend
    players = []
    for item in gathered_data:
        r = item.get("result", {})
        if "players" in r:
            players.extend(r["players"])
        if "player" in r:
            players.append(r["player"])
        if "replacements" in r:
            players.extend(r["replacements"])

    return {
        "response": final_response,
        "trace": trace,
        "tool_calls": tool_calls_log,
        "agent_outputs": {"gathered_data": gathered_data},
        "players": players[:15],
    }


def _summarise(result: dict) -> str:
    if "players" in result:
        return f"{len(result['players'])} players"
    if "player" in result:
        return result["player"].get("name", "found")
    if "replacements" in result:
        return f"{len(result['replacements'])} replacements"
    if "error" in result:
        return f"Error: {result['error']}"
    return "done"