import os
from dotenv import load_dotenv

load_dotenv()


def embed_text(text: str) -> list:
    """Generate 768-dim embedding using Gemini text-embedding-004."""
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        result = client.models.embed_content(
            model="models/text-embedding-004",
            contents=text,
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"[embed_text] Error: {e}")
        return [0.0] * 768


def build_player_stat_string(player: dict) -> str:
    """Convert a player document to a stat string for embedding."""
    return (
        f"position:{player.get('position', '')} "
        f"overall:{player.get('overall_rating', 0)} "
        f"age:{player.get('age', 0)} "
        f"pace:{player.get('pace', 0)} "
        f"shooting:{player.get('shooting', 0)} "
        f"passing:{player.get('passing', 0)} "
        f"dribbling:{player.get('dribbling', 0)} "
        f"defending:{player.get('defending', 0)} "
        f"physic:{player.get('physic', 0)} "
        f"nationality:{player.get('nationality', '')} "
        f"league:{player.get('league_name', '')}"
    )