from db.queries import get_player
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

player1 = input("Player 1: ")
player2 = input("Player 2: ")

p1 = get_player(player1)
p2 = get_player(player2)

prompt = f"""
Compare these players:

Player 1:
{p1}

Player 2:
{p2}

Give:
1. Technical Comparison
2. Physical Comparison
3. Tactical Fit
4. Better Long-Term Option
5. Final Verdict
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

print(response.text)