from db.queries import search_players

query = input("Scout Query: ")

query = query.lower()

if "midfielder" in query:
    players = search_players(
        position="CM",
        max_age=23,
        min_rating=85
    )

    print("\nResults:\n")

    for p in players:
        print(
            f"{p['name']} | "
            f"OVR {p['overall_rating']} | "
            f"Age {p['age']}"
        )

else:
    print("Query not supported yet.")