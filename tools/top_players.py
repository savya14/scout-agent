from db.queries import get_top_players

players = get_top_players(10)

print("\nTop 10 Players:\n")

for player in players:
    print(
        f"{player['name']} | "
        f"OVR {player['overall_rating']} | "
        f"{player['club_name']}"
    )