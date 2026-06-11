import time
from google import genai
from dotenv import load_dotenv
import os
from db.queries import get_player, find_replacements

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_player_summary(player):
    return f"""
Name: {player.get('name', 'N/A')}
Club: {player.get('club_name', 'N/A')}
Position: {player.get('position', 'N/A')}
Rating: {player.get('overall_rating', 'N/A')}
Age: {player.get('age', 'N/A')}
Nationality: {player.get('nationality', 'N/A')}
Pace: {player.get('pace', 'N/A')}
Shooting: {player.get('shooting', 'N/A')}
Passing: {player.get('passing', 'N/A')}
Dribbling: {player.get('dribbling', 'N/A')}
Defending: {player.get('defending', 'N/A')}
Physical: {player.get('physic', 'N/A')}
""".strip()


def build_candidates_text(candidates):
    if not candidates:
        return "No candidates found matching the criteria."
    text = ""
    for i, p in enumerate(candidates[:10], 1):
        text += f"""
Candidate {i}
{build_player_summary(p)}

"""
    return text.strip()


def call_gemini_with_retry(prompt, retries=3, delay=3):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash-latest",
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            return None
    return None


def run_transfer_recommender(player_name, return_data=False):
    player = get_player(player_name)

    if not player:
        if return_data:
            return None
        print(f"Player '{player_name}' not found in database.")
        return

    candidates = find_replacements(
        position=player.get("position", ""),
        current_club=player.get("club_name"),
        max_age=26,
        min_rating=max(70, player.get("overall_rating", 80) - 8),
        reference_rating=player.get("overall_rating")
    )

    if not candidates:
        if return_data:
            return {"error": "No replacement candidates found. Try a different player."}
        print("No candidates found.")
        return

    player_summary = build_player_summary(player)
    candidate_text = build_candidates_text(candidates)

    prompt = f"""
You are an elite football scout working for a top European club.

IMPORTANT RULES:
Output plain text only.
Do not use markdown.
Do not use *, **, ###, -, bullet points, or code blocks.
Do not print Python dictionaries.
Keep the report clean and professional.
Only recommend players from the candidate list provided.
Do not invent players or statistics.

Player Being Replaced

{player_summary}

Replacement Candidates

{candidate_text}

Select the 3 best replacements from the candidates above.
Consider position-specific attributes — a striker needs shooting and pace,
a midfielder needs passing and dribbling, a defender needs defending and physic.

For each replacement use EXACTLY this format:

TOP REPLACEMENT

Name:
Club:
Age:
Rating:

Why He Fits:
(write 3-5 sentences explaining tactical and statistical fit)

Strengths:
(write 3-5 concise strengths relevant to the position)

Risks:
(write 2-3 concise risks)

Then repeat for the second and third player.

Finish with:

FINAL RANKING

1. Player Name - one sentence reason
2. Player Name - one sentence reason
3. Player Name - one sentence reason
"""

    report_text = call_gemini_with_retry(prompt)

    if not report_text:
        if return_data:
            return {"error": "Gemini API is currently unavailable. Please try again in a moment."}
        print("API Error: Could not get response from Gemini.")
        return

    if return_data:
        return {
            "player": player,
            "candidates": candidates,
            "report": report_text
        }

    print("\n")
    print("=" * 70)
    print("TRANSFER RECOMMENDATION REPORT")
    print("=" * 70)
    print(f"Replacing: {player.get('name')} ({player.get('club_name')})")
    print("=" * 70)
    print("\n")
    print(report_text)


if __name__ == "__main__":
    player_name = input("Player to replace: ")
    run_transfer_recommender(player_name)