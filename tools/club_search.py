from db.queries import search_players_by_club

players = search_players_by_club("Barcelona")

for player in players:
    print(player["name"])