from db.queries import search_players

players = search_players(
    position="CM",
    max_age=23,
    min_rating=85
)

for player in players:
    print(
        player["name"],
        player["overall_rating"],
        player["age"]
    )