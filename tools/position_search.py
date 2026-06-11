from db.queries import search_players_by_position

players = search_players_by_position("CM")

for player in players:
    print(player["name"])