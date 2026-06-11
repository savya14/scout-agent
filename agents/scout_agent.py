from google import genai
from dotenv import load_dotenv
import os

from db.queries import search_player_by_name

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

player_name = input("Enter player name: ")

player = search_player_by_name(player_name)

if not player:
    print("Player not found")
    exit()
    
prompt = f"""
You are a football scout.

Analyze this player:

{player}

Give:
1. Strengths
2. Weaknesses
3. Playing style
4. Development potential
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

print(response.text)