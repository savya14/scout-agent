import unicodedata
import pandas as pd
from db.connection import players_collection


def normalize(text: str) -> str:
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8").lower().strip()


def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default


def safe_str(val, default=""):
    try:
        if pd.isna(val):
            return default
        return str(val).strip()
    except:
        return default


print("Loading CSV...")

df = pd.read_csv("data/EAFC26-Men.csv")

# Filter to men's players only
df = df[df["GENDER"] == "M"] if "GENDER" in df.columns else df

players = []

for _, row in df.iterrows():
    raw_position = safe_str(row.get("Position", ""))
    primary_position = raw_position.split(",")[0].strip().upper()

    pace      = safe_int(row.get("PAC"))
    shooting  = safe_int(row.get("SHO"))
    passing   = safe_int(row.get("PAS"))
    dribbling = safe_int(row.get("DRI"))
    defending = safe_int(row.get("DEF"))
    physic    = safe_int(row.get("PHY"))
    overall   = safe_int(row.get("OVR"))

    composite_score = round(
        shooting  * 0.20 +
        dribbling * 0.20 +
        passing   * 0.20 +
        pace      * 0.15 +
        physic    * 0.15 +
        defending * 0.10,
        2
    )

    name = safe_str(row.get("Name"))

    player = {
        "name":             name,
        "name_normalized":  normalize(name),
        "overall_rating":   overall,
        "age":              safe_int(row.get("Age")),
        "nationality":      safe_str(row.get("Nation")),
        "league_name":      safe_str(row.get("League")),
        "club_name":        safe_str(row.get("Team")),
        "position":         primary_position,
        "pace":             pace,
        "shooting":         shooting,
        "passing":          passing,
        "dribbling":        dribbling,
        "defending":        defending,
        "physic":           physic,
        "preferred_foot":   safe_str(row.get("Preferred foot")),
        "height":           safe_str(row.get("Height")),
        "weight":           safe_str(row.get("Weight")),
        "weak_foot":        safe_int(row.get("Weak foot")),
        "skill_moves":      safe_int(row.get("Skill moves")),
        "alt_positions":    safe_str(row.get("Alternative positions")),

        # Detailed attributes
        "acceleration":     safe_int(row.get("Acceleration")),
        "sprint_speed":     safe_int(row.get("Sprint Speed")),
        "finishing":        safe_int(row.get("Finishing")),
        "shot_power":       safe_int(row.get("Shot Power")),
        "long_shots":       safe_int(row.get("Long Shots")),
        "vision":           safe_int(row.get("Vision")),
        "crossing":         safe_int(row.get("Crossing")),
        "short_passing":    safe_int(row.get("Short Passing")),
        "long_passing":     safe_int(row.get("Long Passing")),
        "ball_control":     safe_int(row.get("Ball Control")),
        "agility":          safe_int(row.get("Agility")),
        "reactions":        safe_int(row.get("Reactions")),
        "composure":        safe_int(row.get("Composure")),
        "interceptions":    safe_int(row.get("Interceptions")),
        "heading":          safe_int(row.get("Heading Accuracy")),
        "def_awareness":    safe_int(row.get("Def Awareness")),
        "standing_tackle":  safe_int(row.get("Standing Tackle")),
        "sliding_tackle":   safe_int(row.get("Sliding Tackle")),
        "jumping":          safe_int(row.get("Jumping")),
        "stamina":          safe_int(row.get("Stamina")),
        "strength":         safe_int(row.get("Strength")),
        "aggression":       safe_int(row.get("Aggression")),
        "positioning":      safe_int(row.get("Positioning")),
        "volleys":          safe_int(row.get("Volleys")),
        "penalties":        safe_int(row.get("Penalties")),

        # GK attributes
        "gk_diving":        safe_int(row.get("GK Diving")),
        "gk_handling":      safe_int(row.get("GK Handling")),
        "gk_kicking":       safe_int(row.get("GK Kicking")),
        "gk_positioning":   safe_int(row.get("GK Positioning")),
        "gk_reflexes":      safe_int(row.get("GK Reflexes")),

        # Computed
        "composite_score":  composite_score,
        "value_eur":        0,
        "stats_embedding":  []
    }

    players.append(player)

print(f"Prepared {len(players)} players")

players_collection.delete_many({})
players_collection.insert_many(players)

print(f"✅ Inserted {len(players)} players into MongoDB")

# Create index on name_normalized for fast accent-insensitive lookups
players_collection.create_index("name_normalized")
print("✅ Index created on name_normalized")

# Sanity checks
tests = ["Mbappe", "Julian Alvarez", "Vinicius", "Pedri"]
print("\nAccent search tests:")
for test in tests:
    from db.queries import search_player_by_name
    result = search_player_by_name(test)
    if result:
        print(f"  '{test}' → {result['name']} ({result['club_name']})")
    else:
        print(f"  '{test}' → NOT FOUND")