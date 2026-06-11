import time
from google import genai
from dotenv import load_dotenv
import os

from db.queries import search_player_by_name

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _call_gemini(prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash-latest",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                return f"API error: {e}"
    return ""


def _build_player_block(player: dict) -> str:
    return (
        f"Name: {player.get('name')}\n"
        f"Club: {player.get('club_name')}\n"
        f"Position: {player.get('position')}\n"
        f"Overall: {player.get('overall_rating')}\n"
        f"Age: {player.get('age')}\n"
        f"Nationality: {player.get('nationality')}\n"
        f"Pace: {player.get('pace')} | Shooting: {player.get('shooting')} | "
        f"Passing: {player.get('passing')} | Dribbling: {player.get('dribbling')} | "
        f"Defending: {player.get('defending')} | Physical: {player.get('physic')}"
    )


def agent_debate(player_name: str, session_id: str = "default") -> dict:
    """
    Two AI scouts debate whether to sign a player.
    Scout A argues FOR. Scout B argues AGAINST.
    A third agent gives the final verdict.
    """
    player = search_player_by_name(player_name)
    if not player:
        return {"error": f"Player '{player_name}' not found in database."}

    player_block = _build_player_block(player)

    # ── Scout A: Pro case ─────────────────────────────────────────────────────
    pro_prompt = f"""
You are Scout A, an aggressive talent-hunter who believes in this player.

Player:
{player_block}

Argue WHY your club should sign this player.
Be specific — use the stats, age, position fit, and upside.
Write 4-6 sentences. Plain text only. No markdown.
Sound passionate but professional.
"""
    pro_case = _call_gemini(pro_prompt)
    time.sleep(0.5)

    # ── Scout B: Con case ─────────────────────────────────────────────────────
    con_prompt = f"""
You are Scout B, a cautious analyst who is skeptical about this player.

Player:
{player_block}

Pro scout's argument:
{pro_case}

Argue WHY your club should NOT sign this player, or why there are serious risks.
Counter the pro scout's points directly. Use the stats to find weaknesses.
Write 4-6 sentences. Plain text only. No markdown.
Sound measured and data-driven.
"""
    con_case = _call_gemini(con_prompt)
    time.sleep(0.5)

    # ── Verdict agent ─────────────────────────────────────────────────────────
    verdict_prompt = f"""
You are the Head of Scouting. Two scouts have debated this player.

Player:
{player_block}

Scout A (Pro):
{pro_case}

Scout B (Against):
{con_case}

Give your final verdict and recommendation.
Rules:
- Plain text only. No markdown.
- State clearly: SIGN, DO NOT SIGN, or MONITOR.
- Give a one-paragraph justification.
- Give a confidence score out of 10.
"""
    verdict = _call_gemini(verdict_prompt)

    # Extract recommendation keyword
    verdict_upper = verdict.upper()
    if "DO NOT SIGN" in verdict_upper:
        recommendation = "DO NOT SIGN"
    elif "MONITOR" in verdict_upper:
        recommendation = "MONITOR"
    elif "SIGN" in verdict_upper:
        recommendation = "SIGN"
    else:
        recommendation = "INCONCLUSIVE"

    return {
        "player": player,
        "pro_case": pro_case,
        "con_case": con_case,
        "verdict": verdict,
        "recommendation": recommendation,
    }