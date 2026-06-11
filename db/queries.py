import unicodedata
from db.connection import players_collection


def normalize(text: str) -> str:
    return (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )


PLAYER_NICKNAMES = {
    "vinicius":         "vini jr.",
    "vinicius jr":      "vini jr.",
    "vinicius junior":  "vini jr.",
    "cr7":              "cristiano ronaldo",
    "ronaldo":          "cristiano ronaldo",
    "neymar":           "neymar jr.",
    "messi":            "lionel messi",
    "rudiger":          "antonio rudiger",
    "militao":          "eder militao",
    "tchouameni":       "aurelien tchouameni",
    "camavinga":        "eduardo camavinga",
    "benzema":          "karim benzema",
    "modric":           "luka modric",
    "kroos":            "toni kroos",
    "salah":            "mohamed salah",
    "mane":             "sadio mane",
    "kdb":              "kevin de bruyne",
    "de bruyne":        "kevin de bruyne",
    "son":              "son heung-min",
    "lewandowski":      "robert lewandowski",
    "haaland":          "erling haaland",
    "kane":             "harry kane",
    "rashford":         "marcus rashford",
    "saka":             "bukayo saka",
    "foden":            "phil foden",
    "grealish":         "jack grealish",
    "mount":            "mason mount",
    "rice":             "declan rice",
    "trippier":         "kieran trippier",
    "alisson":          "alisson",
    "ederson":          "ederson",
    "ter stegen":       "marc-andre ter stegen",
    "neuer":            "manuel neuer",
    "oblak":            "jan oblak",
    "courtois":         "thibaut courtois",
    "valverde":         "federico valverde",
    "bellingham":       "jude bellingham",
    "pedri":            "pedri",
    "gavi":             "gavi",
    "yamal":            "lamine yamal",
    "lamine":           "lamine yamal",
    "dembele":          "ousmane dembele",
    "lewandowski":      "robert lewandowski",
    "ferran":           "ferran torres",
    "raphinha":         "raphinha",
    "joao felix":       "joao felix",
    "felix":            "joao felix",
    "griezmann":        "antoine griezmann",
    "atletico":         "atletico de madrid",
    "julian alvarez":   "julian alvarez",
    "alvarez":          "julian alvarez",
    "suarez":           "luis suarez",
    "firmino":          "roberto firmino",
    "nunez":            "darwin nunez",
    "diaz":             "luis diaz",
    "jota":             "diogo jota",
    "salah":            "mohamed salah",
    "van dijk":         "virgil van dijk",
    "robertson":        "andrew robertson",
    "trent":            "trent alexander-arnold",
    "alexander arnold": "trent alexander-arnold",
    "thiago":           "thiago alcantara",
    "fabinho":          "fabinho",
    "henderson":        "jordan henderson",
    "konate":           "ibrahima konate",
    "matip":            "joel matip",
    "gomez":            "joe gomez",
    "kelleher":         "caoimhin kelleher",
    "mbappe":           "kylian mbappe",
    "kylian":           "kylian mbappe",
    "ethan mbappe":     "ethan mbappe",
    "dembele":          "ousmane dembele",
    "hakimi":           "achraf hakimi",
    "marquinhos":       "marquinhos",
    "verratti":         "marco verratti",
    "rabiot":           "adrien rabiot",
    "kimpembe":         "presnel kimpembe",
    "navas":            "keylor navas",
    "donnarumma":       "gianluigi donnarumma",
    "theo":             "theo hernandez",
    "hernandez":        "theo hernandez",
    "leao":             "rafael leao",
    "giroud":           "olivier giroud",
    "tonali":           "sandro tonali",
    "bennacer":         "ismael bennacer",
    "barella":          "nicolo barella",
    "lautaro":          "lautaro martinez",
    "martinez":         "lautaro martinez",
    "lukaku":           "romelu lukaku",
    "dzeko":            "edin dzeko",
    "brozovic":         "marcelo brozovic",
    "perisic":          "ivan perisic",
    "handanovic":       "samir handanovic",
    "skriniar":         "milan skriniar",
    "de vrij":          "stefan de vrij",
    "dumfries":         "denzel dumfries",
    "chiesa":           "federico chiesa",
    "vlahovic":         "dusan vlahovic",
    "dybala":           "paulo dybala",
    "pogba":            "paul pogba",
    "kante":            "n'golo kante",
    "ngolo":            "n'golo kante",
    "giroud":           "olivier giroud",
    "upamecano":        "dayot upamecano",
    "kounde":           "jules kounde",
    "laporte":          "aymeric laporte",
    "ferran":           "ferran torres",
    "busquets":         "sergio busquets",
    "alba":             "jordi alba",
    "pique":            "gerard pique",
    "ter stegen":       "marc-andre ter stegen",
    "carvajal":         "carvajal",
    "nacho":            "nacho",
    "isco":             "isco",
    "asensio":          "marco asensio",
    "rodrygo":          "rodrygo",
    "tchouameni":       "aurelien tchouameni",
    "ceballos":         "dani ceballos",
}


def search_player_by_name(name):
    normalized_input = normalize(name)

    # Check nickname map first
    resolved = PLAYER_NICKNAMES.get(normalized_input, normalized_input)

    # 1. Exact normalized match on resolved name
    result = players_collection.find_one(
        {"name_normalized": normalize(resolved)},
        {"_id": 0}
    )
    if result:
        return result

    # 2. Partial match on resolved name — highest rated wins
    candidates = list(
        players_collection.find(
            {"name_normalized": {"$regex": normalize(resolved), "$options": "i"}},
            {"_id": 0}
        ).sort("overall_rating", -1).limit(5)
    )
    if candidates:
        return candidates[0]

    # 3. If resolved was different from input, try original too
    if resolved != normalized_input:
        candidates = list(
            players_collection.find(
                {"name_normalized": {"$regex": normalized_input, "$options": "i"}},
                {"_id": 0}
            ).sort("overall_rating", -1).limit(5)
        )
        if candidates:
            return candidates[0]

    # 4. Last resort: original name string regex
    candidates = list(
        players_collection.find(
            {"name": {"$regex": name, "$options": "i"}},
            {"_id": 0}
        ).sort("overall_rating", -1).limit(5)
    )
    if candidates:
        return candidates[0]

    return None


def search_players_by_position(position):
    return list(
        players_collection.find(
            {"position": position.upper()},
            {"_id": 0}
        ).limit(10)
    )


def search_players_by_club(club):
    return list(
        players_collection.find(
            {"club_name": {"$regex": club, "$options": "i"}},
            {"_id": 0}
        ).limit(10)
    )


def get_player(name):
    return search_player_by_name(name)


def search_young_players(max_age=23, min_rating=80):
    return list(
        players_collection.find(
            {
                "age": {"$lte": max_age},
                "overall_rating": {"$gte": min_rating}
            },
            {"_id": 0}
        ).limit(20)
    )


def search_players(
    position=None,
    max_age=None,
    min_rating=None,
    nationality=None
):
    query = {}

    if position:
        query["position"] = position.upper()

    if max_age:
        query["age"] = {"$lte": max_age}

    if min_rating:
        query["overall_rating"] = {"$gte": min_rating}

    if nationality:
        query["nationality"] = nationality

    return list(
        players_collection.find(query, {"_id": 0}).limit(20)
    )


POSITION_WEIGHTS = {
    "ST":  {"shooting": 0.40, "pace": 0.30, "physic": 0.20, "dribbling": 0.10},
    "CF":  {"shooting": 0.35, "dribbling": 0.30, "pace": 0.25, "passing": 0.10},
    "LW":  {"dribbling": 0.35, "pace": 0.35, "shooting": 0.20, "passing": 0.10},
    "RW":  {"dribbling": 0.35, "pace": 0.35, "shooting": 0.20, "passing": 0.10},
    "FWD": {"shooting": 0.40, "pace": 0.30, "physic": 0.20, "dribbling": 0.10},
    "CAM": {"passing": 0.35, "dribbling": 0.35, "shooting": 0.20, "pace": 0.10},
    "CM":  {"passing": 0.40, "dribbling": 0.25, "physic": 0.20, "pace": 0.15},
    "CDM": {"defending": 0.40, "physic": 0.30, "passing": 0.20, "pace": 0.10},
    "LM":  {"pace": 0.35, "dribbling": 0.30, "passing": 0.25, "shooting": 0.10},
    "RM":  {"pace": 0.35, "dribbling": 0.30, "passing": 0.25, "shooting": 0.10},
    "MID": {"passing": 0.40, "dribbling": 0.30, "pace": 0.20, "shooting": 0.10},
    "LB":  {"pace": 0.35, "defending": 0.35, "passing": 0.20, "physic": 0.10},
    "RB":  {"pace": 0.35, "defending": 0.35, "passing": 0.20, "physic": 0.10},
    "CB":  {"defending": 0.50, "physic": 0.30, "pace": 0.15, "passing": 0.05},
    "DEF": {"defending": 0.50, "physic": 0.30, "pace": 0.15, "passing": 0.05},
    "GK":  {"gk_diving": 0.25, "gk_handling": 0.25,
             "gk_reflexes": 0.25, "gk_positioning": 0.25},
}

DEFAULT_WEIGHTS = {
    "overall_rating": 0.50,
    "pace": 0.15,
    "shooting": 0.15,
    "passing": 0.10,
    "dribbling": 0.10,
}


def compute_position_score(player, position):
    weights = POSITION_WEIGHTS.get(position.upper(), DEFAULT_WEIGHTS)
    return sum(player.get(stat, 0) * w for stat, w in weights.items())


def find_replacements(
    position,
    current_club=None,
    max_age=26,
    min_rating=75,
    nationality=None,
    preferred_foot=None,
    reference_rating=None
):
    query = {
        "position": position.upper(),
        "age": {"$lte": max_age},
        "overall_rating": {"$gte": min_rating}
    }

    if current_club:
        query["club_name"] = {"$ne": current_club}

    if nationality:
        query["nationality"] = nationality

    if preferred_foot:
        query["preferred_foot"] = preferred_foot

    if reference_rating:
        query["overall_rating"] = {
            "$gte": min_rating,
            "$lte": reference_rating + 2
        }

    players = list(
        players_collection.find(query, {"_id": 0})
        .sort("overall_rating", -1)
        .limit(50)
    )

    for p in players:
        p["_score"] = compute_position_score(p, position)

    players.sort(key=lambda x: x["_score"], reverse=True)

    for p in players:
        p.pop("_score", None)

    return players[:20]


def get_top_players(limit=10):
    return list(
        players_collection.find({}, {"_id": 0})
        .sort("overall_rating", -1)
        .limit(limit)
    )


if __name__ == "__main__":
    print("=== Messi ===")
    print(search_player_by_name("Messi"))

    print("\n=== Top 5 Players ===")
    for player in get_top_players(5):
        print(player["name"], "-", player["overall_rating"])