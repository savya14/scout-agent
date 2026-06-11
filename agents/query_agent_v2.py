from google import genai
from dotenv import load_dotenv
import os
import json
from db.queries import search_players

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def run_query_agent(query: str) -> dict:
    prompt = f"""
Extract scouting filters from this query.
Query: {query}

Return ONLY valid JSON with these exact keys (omit keys not mentioned):
{{
  "position": "CM",
  "max_age": 23,
  "min_rating": 85,
  "nationality": "Spain"
}}

Position values must be one of: GK, CB, LB, RB, CDM, CM, CAM, LM, RM, LW, RW, CF, ST
"""
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=prompt
        )
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        filters = json.loads(text)
    except Exception as e:
        return {"error": f"Failed to parse query: {str(e)}", "filters": {}, "players": []}

    players = search_players(
        position=filters.get("position"),
        max_age=filters.get("max_age"),
        min_rating=filters.get("min_rating"),
        nationality=filters.get("nationality")
    )

    return {
        "filters": filters,
        "players": players
    }


if __name__ == "__main__":
    query = input("Scout Query: ")
    result = run_query_agent(query)
    print(f"\nFilters: {result['filters']}")
    print(f"\nResults ({len(result['players'])} players):\n")
    for p in result["players"]:
        print(f"{p['name']} | OVR {p['overall_rating']} | Age {p['age']} | {p['nationality']}")