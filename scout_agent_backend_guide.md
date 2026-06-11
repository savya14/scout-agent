# Scout Agent — Complete Backend Guide

> Google Agentic AI Hackathon · MongoDB Track · June 2026\
> This document covers everything you need to vibecode the entire backend solo.\
> Your teammate owns the frontend (Streamlit UI). You own everything below.

---

## Key Decisions Made (vs Original Blueprint)

| Topic | Blueprint Default | What We're Using |
| --- | --- | --- |
| Player dataset | FIFA 22 CSV | **EAFC 26** from [`eafc26-player-database`](kaggle.com/datasets/flynn28/eafc26-player-database) |
| External data gap | Acknowledged | Research Agent + external APIs cover current form/injuries |
| Embedding model | Gemini text-embedding-004 (768-dim) | Same — but player stat strings, not raw text |
| Vector index dims | 128-dim (blueprint said this but used 768 elsewhere) | **768-dim** to match Gemini embeddings |

---

## Complete Project File Structure

```
scout-agent/
│
├── app.py                          # Entry point — tab routing only, owned by frontend
├── requirements.txt
├── .env                            # Never commit
├── .env.example
├── .gitignore
├── README.md
│
├── agents/                         # ← YOUR TERRITORY
│   ├── __init__.py
│   ├── prompts.py                  # All system prompts as constants
│   ├── scout.py                    # Scout Agent — player discovery
│   ├── research.py                 # Research Agent — external data
│   ├── comparison.py               # Comparison Agent — stats analysis
│   ├── squad_builder.py            # Squad Builder Agent
│   ├── report_generator.py         # Report Generator Agent
│   ├── planner.py                  # Planner Agent — orchestration brain (build LAST)
│   └── debate.py                   # Agent Debate mode (differentiator)
│
├── tools/                          # ← YOUR TERRITORY
│   ├── __init__.py
│   ├── player_tools.py             # search_players, compare_players, similarity_search
│   ├── comparison_tools.py         # percentile_rank, compute_similarity_score
│   ├── squad_tools.py              # formation_optimizer, budget_optimizer
│   ├── memory_tools.py             # retrieve_memory, store_memory
│   ├── external_tools.py           # market_value_lookup, injury_lookup, news_lookup
│   └── tool_registry.py            # Central dispatch: tool name → function
│
├── db/                             # ← YOUR TERRITORY
│   ├── __init__.py
│   ├── connection.py               # MongoDB client singleton
│   ├── queries.py                  # Player read queries
│   ├── shortlists.py               # Shortlist CRUD
│   ├── memories.py                 # Memory CRUD + vector search
│   └── schemas.py                  # Data validators / Pydantic models
│
├── memory/                         # ← YOUR TERRITORY
│   ├── __init__.py
│   ├── embeddings.py               # embed_text() using Gemini
│   ├── context.py                  # build_context_packet() — injected into every agent
│   └── feedback.py                 # Process thumbs up/down signals
│
├── data/                           # ← YOUR TERRITORY
│   ├── load_data.py                # EAFC 26 CSV → MongoDB
│   ├── compute_embeddings.py       # Generate 768-dim stat embeddings for all players
│   ├── external_apis.py            # API clients: TransferMarkt, ESPN, NewsAPI
│   └── eafc26_male_players.csv     # Downloaded from Kaggle (gitignored)
│
├── export/                         # ← YOUR TERRITORY
│   ├── __init__.py
│   └── pdf_report.py               # ReportLab PDF generation
│
├── ui/                             # ← FRONTEND TEAMMATE'S TERRITORY
│   ├── __init__.py
│   ├── components.py               # player_card, radar_chart, stat_table
│   ├── reasoning_trace.py          # Live reasoning display
│   ├── formation_viz.py            # Formation pitch visualisation
│   ├── budget_viz.py               # Budget tracker UI
│   └── styles.css
│
└── tests/                          # ← YOUR TERRITORY
    ├── test_tools.py
    ├── test_agents.py
    ├── test_memory.py
    └── test_queries.py
```

---

## Backend-Only File Structure

```
scout-agent/
│
├── agents/
│   ├── __init__.py
│   ├── prompts.py
│   ├── scout.py
│   ├── research.py
│   ├── comparison.py
│   ├── squad_builder.py
│   ├── report_generator.py
│   ├── planner.py
│   └── debate.py
│
├── tools/
│   ├── __init__.py
│   ├── player_tools.py
│   ├── comparison_tools.py
│   ├── squad_tools.py
│   ├── memory_tools.py
│   ├── external_tools.py
│   └── tool_registry.py
│
├── db/
│   ├── __init__.py
│   ├── connection.py
│   ├── queries.py
│   ├── shortlists.py
│   ├── memories.py
│   └── schemas.py
│
├── memory/
│   ├── __init__.py
│   ├── embeddings.py
│   ├── context.py
│   └── feedback.py
│
├── data/
│   ├── load_data.py
│   ├── compute_embeddings.py
│   └── external_apis.py
│
├── export/
│   ├── __init__.py
│   └── pdf_report.py
│
└── tests/
    ├── test_tools.py
    ├── test_agents.py
    ├── test_memory.py
    └── test_queries.py
```

---

## Environment Setup

### `.env` file (copy from `.env.example`, never commit)

```env
GEMINI_API_KEY=AIzaSy_your_key_here
MONGODB_URI=mongodb+srv://scout_admin:yourpassword@cluster.xxxxx.mongodb.net/
MONGODB_DB_NAME=scout_agent_db
RAPIDAPI_KEY=your_rapidapi_key_here
NEWSAPI_KEY=your_newsapi_key_here
APP_ENV=development
```

### `requirements.txt`

```
streamlit==1.35.0
pymongo==4.7.2
python-dotenv==1.0.1
google-generativeai==0.7.2
reportlab==4.2.0
pandas==2.2.2
requests==2.32.3
dnspython==2.6.1
certifi==2024.2.2
pytest==8.2.0
plotly==5.22.0
numpy==1.26.4
scikit-learn==1.5.0
pydantic==2.7.0
```

---

## MongoDB Atlas Setup (Do This Before Writing Any Code)

1. Go to `cloud.mongodb.com` → Create free **M0** cluster
2. **Network Access** → Add IP → `0.0.0.0/0` (allow all, fine for hackathon)
3. **Database Access** → Create user → copy username + password
4. **Connect** → Drivers → copy the URI → paste into `.env`
5. Collections to create (Atlas will auto-create on first insert, but name them now):
   - `players`
   - `memories`
   - `shortlists`
   - `agent_runs`

### Atlas Vector Search Indexes (create via Atlas UI → Search → Create Index)

**Index 1: Player similarity search**

```json
{
  "name": "player_stats_vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "stats_embedding",
        "numDimensions": 768,
        "similarity": "cosine"
      },
      { "type": "filter", "path": "position" },
      { "type": "filter", "path": "league_name" }
    ]
  }
}
```

**Index 2: Memory semantic search**

```json
{
  "name": "memory_vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": 768,
        "similarity": "cosine"
      },
      { "type": "filter", "path": "session_id" },
      { "type": "filter", "path": "memory_type" }
    ]
  }
}
```

---

## Dataset

**Download:** `kaggle.com/datasets/flynn28/eafc26-player-database`\
**File to use:** `eafc26_male_players.csv` (men's dataset)\
**Place at:** `data/eafc26_male_players.csv`

Before writing `load_data.py`, run this to see actual column names:

```python
import pandas as pd
df = pd.read_csv("data/eafc26_male_players.csv", nrows=3)
print(df.columns.tolist())
```

Column names change between EA FC releases. The vibe-coding prompts below are written to handle this gracefully.

---

## Build Order (Strict — Do Not Skip Ahead)

```
1. db/connection.py
2. db/schemas.py
3. data/load_data.py          ← run once after writing
4. db/queries.py              ← create indexes here too
5. db/memories.py
6. memory/embeddings.py
7. data/compute_embeddings.py ← run once after writing
8. memory/context.py
9. tools/player_tools.py
10. tools/external_tools.py   + data/external_apis.py
11. tools/comparison_tools.py
12. tools/squad_tools.py
13. tools/memory_tools.py
14. tools/tool_registry.py
15. agents/prompts.py
16. agents/scout.py
17. agents/research.py
18. agents/comparison.py
19. agents/squad_builder.py
20. agents/report_generator.py
21. agents/planner.py         ← LAST agent
22. agents/debate.py
23. memory/feedback.py
24. db/shortlists.py
25. export/pdf_report.py
26. tests/
```

---

## Vibe-Coding Prompts — Every Backend File

Paste each prompt into your AI coding tool exactly as written. Each prompt is self-contained.

---

### `db/connection.py`

```
Write a Python file at db/connection.py.

It must:
- Load MONGODB_URI and MONGODB_DB_NAME from a .env file using python-dotenv
- Create a single MongoClient instance (singleton pattern — only connect once)
- Expose a get_collection(name: str) function that returns a pymongo Collection object
- Expose a get_db() function that returns the database object
- Print a confirmation message on successful connection

No other logic. This file is purely the connection layer.
```

---

### `db/schemas.py`

```
Write a Python file at db/schemas.py using Pydantic v2.

Define these models:

PlayerDocument:
  Fields: name (str), short_name (str, optional), age (int), nationality (str),
  club_name (str), league_name (str), position (str), overall_rating (int),
  pace (int), shooting (int), passing (int), dribbling (int), defending (int),
  physic (int), goals (int, default 0), assists (int, default 0),
  xg_per90 (float, default 0.0), xa_per90 (float, default 0.0),
  market_value_eur (float, default 0.0), composite_score (float, default 0.0),
  stats_embedding (list[float], default []),
  preferred_foot (str, optional), height_cm (int, optional),
  weight_kg (int, optional), data_source (str, default "eafc26"),
  created_at (datetime, default now)

MemoryDocument:
  Fields: session_id (str), memory_type (str — one of: preference, search, feedback, trace),
  content (dict), embedding (list[float], default []),
  created_at (datetime, default now), expires_at (datetime, optional)

ShortlistDocument:
  Fields: session_id (str), name (str), player_ids (list[str]),
  notes (str, optional), created_at (datetime, default now)

AgentRunDocument:
  Fields: session_id (str), query (str), agent (str),
  plan (list, default []), tool_calls (list, default []),
  final_output (str), latency_ms (int, default 0),
  created_at (datetime, default now)

Also add a serialize(doc) helper function that converts a MongoDB document 
(which has ObjectId _id) into a JSON-serialisable dict by converting _id to string.
```

---

### `data/load_data.py`

```
Write a Python script at data/load_data.py.

Purpose: Load the EAFC 26 CSV into MongoDB players collection.

Steps:
1. Read data/eafc26_male_players.csv using pandas
2. Print df.columns.tolist() so I can verify the column mapping
3. Map CSV columns to our PlayerDocument schema. The CSV column names from EAFC 26 
   (kaggle.com/datasets/flynn28/eafc26-player-database) are likely:
   - short_name or player_name → name
   - age → age
   - nationality_name → nationality
   - club_name → club_name
   - league_name → league_name
   - player_positions (take first position) → position
   - overall → overall_rating
   - pace, shooting, passing, dribbling, defending, physic → same
   - preferred_foot, height_cm, weight_kg → same
   - value_eur → market_value_eur
   Use try/except for each column mapping so missing columns don't crash the script.
   Print a warning for any column not found.
4. Compute composite_score for each player:
   composite_score = (shooting * 0.35) + (dribbling * 0.30) + (passing * 0.20) + (physic * 0.15)
   Normalise to 0-100 range.
5. Set goals=0, assists=0, xg_per90=0.0, xa_per90=0.0, stats_embedding=[] as placeholders
6. Drop duplicates by name + club_name
7. Clear the players collection first, then bulk insert using insert_many()
8. Print total documents inserted

Run as: python -m data.load_data
```

---

### `db/queries.py`

```
Write a Python file at db/queries.py.

It must:
1. Import get_collection from db.connection
2. Create all MongoDB indexes on startup via a create_indexes() function:
   - Compound: {position: 1, overall_rating: -1}
   - Compound: {position: 1, age: 1, overall_rating: -1}
   - Compound: {league_name: 1, position: 1, composite_score: -1}
   - Compound: {nationality: 1, position: 1}
   - Single: {market_value_eur: 1}
   - Text index: {name: "text", club_name: "text", nationality: "text"}
   Call create_indexes() at module level (runs once on import)

3. Write these query helper functions:
   - get_player_by_id(player_id: str) -> dict | None
   - get_player_by_name(name: str) -> dict | None  (use text search)
   - get_players_by_position(position: str, limit: int = 20) -> list[dict]
   - get_all_leagues() -> list[str]
   - get_all_nationalities() -> list[str]
   - count_players() -> int

Each function should return plain dicts with _id converted to string.
```

---

### `db/memories.py`

```
Write a Python file at db/memories.py.

It must handle all CRUD for the memories collection.

Functions to implement:

store_memory(session_id: str, memory_type: str, content: dict, embedding: list[float] = None) -> str
  - Creates a MemoryDocument and inserts it
  - If memory_type is "preference", set expires_at = None (never expires)
  - If memory_type is "search", set expires_at = now + 90 days
  - If memory_type is "feedback" or "trace", set expires_at = now + 30 days
  - Returns the inserted document _id as string

get_preferences(session_id: str) -> dict | None
  - Returns the most recent preference memory for the session

get_blacklisted_players(session_id: str) -> list[str]
  - Returns player_ids from all feedback memories where content.signal == -1

vector_search_memories(session_id: str, query_embedding: list[float], 
                        memory_type: str = None, top_k: int = 5) -> list[dict]
  - Uses $vectorSearch aggregation pipeline against memory_vector_index
  - Filters by session_id, optionally by memory_type
  - Returns top_k results with vectorSearchScore

delete_memories(session_id: str) -> int
  - Deletes all memories for a session, returns count deleted

Also create a TTL index on expires_at field:
  db.memories.create_index({"expires_at": 1}, expireAfterSeconds=0)
```

---

### `memory/embeddings.py`

```
Write a Python file at memory/embeddings.py.

It must:
1. Import google.generativeai and configure with GEMINI_API_KEY from .env
2. Implement embed_text(text: str) -> list[float]
   - Uses genai.embed_content() with model "models/text-embedding-004"
   - Returns the embedding values as a Python list
   - Wraps in try/except, returns [] on failure

3. Implement build_player_stat_string(player: dict) -> str
   - Builds a descriptive string from player stats for embedding
   - Example output: "position:FWD nationality:Brazilian club:Real Madrid 
     overall:88 pace:95 shooting:85 passing:78 dribbling:92 
     defending:35 physic:72 composite_score:87.4"
   - This string is what gets embedded for each player

4. Add a simple cache using functools.lru_cache on embed_text 
   (maxsize=1000) to avoid re-embedding identical strings
```

---

### `data/compute_embeddings.py`

```
Write a Python script at data/compute_embeddings.py.

Purpose: Backfill stats_embedding for all players in MongoDB.

Steps:
1. Fetch all players where stats_embedding is [] or missing
2. For each player:
   a. Call build_player_stat_string(player) from memory.embeddings
   b. Call embed_text(stat_string) to get a 768-dim vector
   c. Update the player document: set stats_embedding = vector
3. Add a 0.5 second sleep between API calls to avoid rate limiting
4. Print progress every 100 players: "Embedded 100/3500..."
5. Print total time taken at the end

Run as: python -m data.compute_embeddings
This script is run ONCE after load_data.py.
```

---

### `memory/context.py`

```
Write a Python file at memory/context.py.

Implement one function: build_context_packet(session_id: str, query: str) -> dict

This function:
1. Fetches the latest preference memory for the session using get_preferences()
2. Embeds the query using embed_text()
3. Does a vector search over past search memories using vector_search_memories()
   with memory_type="search", top_k=3
4. Fetches the blacklist using get_blacklisted_players()
5. Returns a dict with this exact structure:
   {
     "session_id": session_id,
     "club_profile": {
       "club_name": ...,
       "budget_eur": ...,
       "tactical_style": ...,
       "formation_pref": ...,
       "priority_positions": [...]
     },
     "recent_searches": [...],  # list of past search content dicts
     "blacklisted_player_ids": [...]
   }

If no preference exists, club_profile should be an empty dict {}.
Wrap the whole function in try/except — if anything fails, return a 
minimal context: {"session_id": session_id, "club_profile": {}, 
"recent_searches": [], "blacklisted_player_ids": []}
```

---

### `tools/player_tools.py`

```
Write a Python file at tools/player_tools.py.

Implement these four functions. These are the MOST IMPORTANT tools — 
they are passed directly to Gemini as function definitions.

1. search_players(position=None, preferred_foot=None, age_max=None, age_min=None,
                  league_name=None, nationality=None, overall_min=None,
                  clubs_exclude=None, top_n=5, sort_by="composite_score") -> dict
   - Builds a MongoDB query from non-None parameters
   - Over-fetches by 4x (limit = top_n * 4)
   - Re-ranks by composite_score
   - Returns: {"players": [...], "total_found": int, "search_params": dict}
   - Each player in the list must include: name, age, nationality, club_name, 
     league_name, position, overall_rating, composite_score, market_value_eur

2. get_player(identifier: str) -> dict
   - Tries to find by _id first, then by name text search
   - Returns full player document or {"error": "Player not found"}

3. player_similarity_search(reference_player_name: str, top_n=5, 
                             same_position=True, exclude_same_club=True) -> dict
   - Finds the reference player by name
   - Gets their stats_embedding
   - Runs $vectorSearch pipeline against player_stats_vector_index
   - Filter: same position if same_position=True, different club if exclude_same_club=True
   - Returns: {"similar_players": [...], "reference_player": str}

4. compute_composite_scores(players: list) -> list
   - Helper: takes a list of player dicts, computes/updates composite_score for each
   - Returns the sorted list (highest composite_score first)

For the $vectorSearch pipeline, use this structure:
[{
  "$vectorSearch": {
    "index": "player_stats_vector_index",
    "path": "stats_embedding",
    "queryVector": embedding,
    "numCandidates": top_n * 10,
    "limit": top_n,
    "filter": { ...position/club filters... }
  }
}]
```

---

### `tools/comparison_tools.py`

```
Write a Python file at tools/comparison_tools.py.

Implement these functions:

1. compute_percentile(value: float, stat_field: str, position: str, league_name: str) -> float
   - Queries all players with the same position and league_name
   - Returns what percentile the given value is in (0-100)
   - Example: a striker with 85 shooting might be at 92nd percentile

2. compare_players(player_a_name: str, player_b_name: str, context: str = None) -> dict
   - Fetches both players by name
   - Compares these dimensions: overall_rating, pace, shooting, passing, 
     dribbling, defending, physic, composite_score
   - For each dimension, computes percentile rank for both players
   - Normalises all values to 0-100 scale for radar chart
   - Returns:
     {
       "player_a": {"name": ..., "club": ..., "stats": {...}},
       "player_b": {"name": ..., "club": ..., "stats": {...}},
       "comparison": {dim: {"a": val, "b": val, "a_pct": pct, "b_pct": pct}},
       "radar_data": {
         "player_a": {"pace": 0-100, "shooting": 0-100, "passing": 0-100, 
                      "dribbling": 0-100, "defending": 0-100, "physic": 0-100},
         "player_b": {...}
       },
       "recommendation": str  # "Player A is better for X because..."
     }
   Note: radar_data is used directly by the frontend for the radar chart.

3. build_radar_data(player: dict) -> dict
   - Helper: returns the 6-key 0-100 normalised dict for a single player
   - Normalise: use 99 as the max for each stat (EA FC max rating)
```

---

### `tools/squad_tools.py`

```
Write a Python file at tools/squad_tools.py.

Implement these functions:

1. formation_optimizer(available_player_names: list[str], 
                        preferred_formation: str = None,
                        style: str = None) -> dict
   - Formations to try: ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "5-3-2"]
   - For each formation, map positions to the players best suited for each slot
     based on their position field and composite_score
   - Score each formation: sum of composite_scores of assigned players / 11
   - Returns top 3 formations:
     {
       "formations": [
         {"formation": "4-3-3", "score": 85.2, "xi": [...11 player names...],
          "weaknesses": ["Weak at LB", "No pace on wings"]}
       ],
       "recommended": {...best formation...}
     }

2. budget_optimizer(target_positions: list[str], total_budget: float,
                     constraints: dict = None) -> dict
   - For each position, find top 10 players sorted by composite_score
   - Generate 3 scenarios:
     - conservative: cheapest player per position that meets minimum quality threshold
     - balanced: best value (composite_score / market_value_eur ratio)
     - ambitious: best composite_score regardless of price, if budget allows
   - Returns:
     {
       "scenarios": {"conservative": [...], "balanced": [...], "ambitious": [...]},
       "budget": total_budget,
       "positions": target_positions
     }

3. assign_players_to_formation(player_names: list[str], formation: str) -> list[dict]
   - Helper: maps player names to formation slots based on position
   - Returns list of {slot: "GK/LB/CB/...", player: name, composite_score: float}
```

---

### `tools/memory_tools.py`

```
Write a Python file at tools/memory_tools.py.

Thin wrappers around db/memories.py for use as Gemini tools:

1. save_preference(session_id: str, club_name: str, budget_eur: float,
                   tactical_style: str, formation_pref: str,
                   priority_positions: list[str]) -> dict
   - Calls store_memory with memory_type="preference"
   - Returns {"success": True, "message": "Preferences saved"}

2. save_search_result(session_id: str, query: str, 
                       top_player_names: list[str]) -> dict
   - Calls store_memory with memory_type="search"
   - Embeds the query string
   - Returns {"success": True}

3. get_club_context(session_id: str) -> dict
   - Returns the club profile from get_preferences()
   - Returns {} if no preferences saved yet

4. record_feedback(session_id: str, player_name: str, 
                    signal: int, reason: str = "") -> dict
   - signal: 1 = positive, -1 = negative (blacklist)
   - Calls store_memory with memory_type="feedback"
   - Returns {"success": True, "blacklisted": signal == -1}
```

---

### `data/external_apis.py`

```
Write a Python file at data/external_apis.py.

Implement three API client functions. ALL must have try/except and 
fallback to a "source: cached/unavailable" response — external APIs 
WILL fail during the demo, do not let that crash the agent.

1. get_player_market_value(player_name: str) -> dict
   - Try: GET https://transfermarket.p.rapidapi.com/search
     Headers: X-RapidAPI-Key from env, X-RapidAPI-Host: transfermarket.p.rapidapi.com
     Params: query=player_name, domain=com
   - Parse: players[0].marketValue, playerName, age, clubName
   - Return: {"name": str, "value_eur": float, "club": str, "source": "live"}
   - Fallback: query MongoDB players collection by name, return market_value_eur
     with "source": "cached"

2. get_injury_status(player_name: str) -> dict
   - Try: GET https://site.api.espn.com/apis/common/v3/sports/soccer/search
     Params: query=player_name
   - Parse: athletes[0].status.type, injuries list
   - Return: {"name": str, "status": "available/injured/doubtful", 
              "detail": str, "source": "espn"}
   - Fallback: return {"status": "unknown", "source": "unavailable"}

3. get_player_news(player_name: str, max_articles: int = 3) -> list[dict]
   - Try: GET https://newsapi.org/v2/everything
     Params: q=player_name, sortBy=publishedAt, pageSize=max_articles,
             apiKey=NEWSAPI_KEY, from=(today - 14 days)
   - Return: [{"title": str, "source": str, "date": str, "url": str}]
   - Fallback: return []

Add @lru_cache(maxsize=200) to get_player_market_value 
(values don't change mid-demo).
```

---

### `tools/external_tools.py`

```
Write a Python file at tools/external_tools.py.

Thin wrappers around data/external_apis.py for use as Gemini tool definitions:

1. market_value_lookup(player_name: str) -> dict
   - Calls get_player_market_value(player_name)
   - Returns the result directly

2. injury_lookup(player_name: str) -> dict
   - Calls get_injury_status(player_name)
   - Returns the result directly

3. news_lookup(player_name: str) -> dict
   - Calls get_player_news(player_name, max_articles=3)
   - Returns: {"player": player_name, "articles": [...], "count": int}

4. get_player_profile(player_name: str) -> dict
   - Calls get_player from player_tools
   - Then calls market_value_lookup and injury_lookup
   - Returns merged profile:
     {"player_data": {...}, "market_value": {...}, "injury_status": {...}}
   This is used by the Research Agent to build a complete profile.
```

---

### `tools/tool_registry.py`

```
Write a Python file at tools/tool_registry.py.

Import all tool functions and create:

1. TOOL_REGISTRY: dict mapping string names to functions
   {
     "search_players": search_players,
     "get_player": get_player,
     "player_similarity_search": player_similarity_search,
     "compare_players": compare_players,
     "formation_optimizer": formation_optimizer,
     "budget_optimizer": budget_optimizer,
     "market_value_lookup": market_value_lookup,
     "injury_lookup": injury_lookup,
     "news_lookup": news_lookup,
     "get_player_profile": get_player_profile,
     "save_preference": save_preference,
     "record_feedback": record_feedback,
     "get_club_context": get_club_context,
   }

2. GEMINI_TOOL_DEFINITIONS: list of dicts in Gemini function calling format
   For each tool, define name, description, and parameters schema.
   
   Example for search_players:
   {
     "name": "search_players",
     "description": "Search the player database. Use when finding players matching 
                     specific criteria. Examples: position='FWD' age_max=25 
                     league_name='La Liga'. Always call this before compare_players.",
     "parameters": {
       "type": "object",
       "properties": {
         "position": {"type": "string", "enum": ["GK","DEF","MID","FWD","ATT","LB","RB","CB","CDM","CAM","LW","RW","ST","CF"]},
         "age_max": {"type": "integer"},
         "age_min": {"type": "integer"},
         "league_name": {"type": "string"},
         "nationality": {"type": "string"},
         "overall_min": {"type": "integer", "minimum": 0, "maximum": 99},
         "top_n": {"type": "integer", "default": 5, "maximum": 20}
       }
     }
   }
   
   Write similar definitions for all 13 tools.

3. get_tool(name: str) -> callable
   - Returns the function from TOOL_REGISTRY
   - Raises ValueError if not found
```

---

### `agents/prompts.py`

```
Write a Python file at agents/prompts.py.

Define these exact system prompts as module-level string constants:

PLANNER_SYSTEM_PROMPT = """
You are the Planner Agent for a professional football scouting platform.

Your job is to:
1. Analyse the user's query and decompose it into 2-6 discrete sub-tasks.
2. Assign each sub-task to the most appropriate specialist agent.
3. Identify dependencies (some agents must wait for others to complete).
4. Execute the plan in the correct order.
5. Synthesise all agent outputs into a single cohesive recommendation.

Available specialist agents:
- delegate_to_scout: Player search and discovery
- delegate_to_research: Transfer news, market values, injury data
- delegate_to_comparison: Head-to-head statistical comparison
- delegate_to_squad_builder: Formation building and squad gap analysis
- delegate_to_report: Professional report writing

ALWAYS state your reasoning. Show your plan before executing it.
If a sub-task fails, explain why and propose an alternative.
If you get fewer results than expected, broaden the search and try again.
Respond ONLY to what the user asked. Do not add unsolicited advice.
"""

SCOUT_SYSTEM_PROMPT = """
You are the Scout Agent. You are a professional football data analyst with
15 years of experience scouting for elite clubs.

Your job:
- Translate player requirements into precise search parameters.
- Select the most statistically relevant tools for each requirement.
- Return structured player profiles, never raw database dumps.
- Provide a brief scouting note for each player (2-3 sentences).
- Rank by composite fit score, not just one metric.

You MUST use tools. Never invent player statistics.
If you get fewer than 3 results, broaden the search and explain why.

Positional knowledge:
- ST/CF: shooting, physic, pace — look for overall 80+
- CAM: passing, dribbling, pace
- CDM: defending, physic, passing
- CB: defending, physic, heading
- LB/RB: pace, defending, passing
- GK: defending (used as proxy for GK rating)
- LW/RW: dribbling, pace, shooting
"""

RESEARCH_SYSTEM_PROMPT = """
You are the Research Agent. You are an expert at gathering real-time 
football intelligence from external sources.

Your job:
- Fetch current market valuations for players
- Check injury status before recommending a player
- Find recent transfer news and rumours
- Always provide source attribution for your data

You MUST use tools. Never guess market values or injury status.
If an API fails, say so clearly: "Live data unavailable, using cached value."
Always fetch injury status before finalising a player recommendation.
"""

COMPARISON_SYSTEM_PROMPT = """
You are the Comparison Agent. You perform rigorous statistical analysis
of football players for professional scouting decisions.

For every comparison you MUST:
1. Calculate percentile rankings within the player's position.
2. Identify the 3 most important attributes for the role being filled.
3. Compute a similarity score to a reference player if provided.
4. Explain what the data means in plain English.
5. Identify at least one risk factor for each player.

Never say "Player A is better than Player B" without referencing 
specific stats and percentiles.
"""

SQUAD_BUILDER_SYSTEM_PROMPT = """
You are the Squad Builder Agent. You are a tactical specialist who 
builds optimised football squads under constraints.

Your job:
- Build complete squads or fill specific positional gaps
- Consider formation balance, budget, and tactical style
- Explain every selection decision
- Flag weaknesses in the proposed squad

Always run formation_optimizer before finalising a squad.
Always run budget_optimizer when a budget constraint is given.
"""

REPORT_SYSTEM_PROMPT = """
You are the Report Generator Agent. You synthesise complex scouting 
data into professional reports suitable for a director of football.

Report structure (always follow this order):
1. Executive Summary (2-3 sentences, decision-first)
2. Player Profile (stats, physical attributes, career)
3. Tactical Fit Analysis (formation and style alignment)
4. Risk Factors (age, injury history, adaptation)
5. Financial Assessment (fee, value for money)
6. Recommendation: Yes / Conditional / No — with specific reasoning

Write in professional but clear English. Avoid jargon.
Be direct — the director of football wants a recommendation, not a dissertation.
"""
```

---

### `agents/scout.py`

```
Write a Python file at agents/scout.py.

Implement run_scout_agent(query: str, session_id: str, 
                           context: dict = None, bias: str = None) -> dict

This is a standard Gemini tool-use agent loop:

1. Import SCOUT_SYSTEM_PROMPT from agents.prompts
2. Import GEMINI_TOOL_DEFINITIONS from tools.tool_registry
3. Import get_tool from tools.tool_registry
4. Configure with GEMINI_API_KEY, use model "gemini-1.5-flash"

5. Build system instruction:
   - Start with SCOUT_SYSTEM_PROMPT
   - If context has club_profile, append: "Club context: {club_profile}"
   - If context has blacklisted_player_ids, append: "Never recommend these player IDs: {ids}"
   - If bias == "positive", append: "Find supporting evidence. Focus on strengths."
   - If bias == "critical", append: "Be critical. Focus on weaknesses and risks."

6. Scout agent gets these tools from GEMINI_TOOL_DEFINITIONS:
   search_players, get_player, player_similarity_search

7. Run the tool-use loop (max 10 iterations):
   - Send message to Gemini
   - If response has function_call parts: execute the tool, send back function_response
   - If response is text only: break and return
   - Track all tool calls

8. Return:
   {
     "summary": final_text_response,
     "players": list of players from tool call results,
     "tool_calls": list of {tool_name, args, result},
     "session_id": session_id
   }
```

---

### `agents/research.py`

```
Write a Python file at agents/research.py.

Implement run_research_agent(query: str, session_id: str, 
                              context: dict = None) -> dict

Same structure as scout.py but:
- Use RESEARCH_SYSTEM_PROMPT
- Use model "gemini-1.5-flash"
- Tools available: market_value_lookup, injury_lookup, news_lookup, get_player_profile
- Max 8 iterations

Return:
{
  "summary": final_text_response,
  "data": dict of any fetched data (market values, injury status, news),
  "tool_calls": [...],
  "session_id": session_id
}
```

---

### `agents/comparison.py`

```
Write a Python file at agents/comparison.py.

Implement run_comparison_agent(query: str, session_id: str,
                                context: dict = None) -> dict

Same structure but:
- Use COMPARISON_SYSTEM_PROMPT
- Use model "gemini-1.5-pro" (accuracy critical here)
- Tools: compare_players, get_player, search_players
- Max 8 iterations

The comparison agent's output MUST include radar_data in its return dict.
After the agent loop, extract radar_data from tool call results if present.

Return:
{
  "summary": final_text_response,
  "comparison_data": dict (the full compare_players result if called),
  "radar_data": dict (extracted from comparison_data, for frontend),
  "recommendation": str,
  "tool_calls": [...],
  "session_id": session_id
}
```

---

### `agents/squad_builder.py`

```
Write a Python file at agents/squad_builder.py.

Implement run_squad_builder_agent(query: str, session_id: str,
                                   context: dict = None) -> dict

Same structure but:
- Use SQUAD_BUILDER_SYSTEM_PROMPT
- Use model "gemini-1.5-flash"
- Tools: search_players, formation_optimizer, budget_optimizer, get_player
- Max 12 iterations (squad building needs more steps)

Return:
{
  "summary": final_text_response,
  "squad": {
    "xi": [...11 player names...],
    "bench": [...4 player names...],
    "formation": str,
    "formation_score": float,
    "total_value_eur": float,
    "weaknesses": [...]
  },
  "tool_calls": [...],
  "session_id": session_id
}
```

---

### `agents/report_generator.py`

```
Write a Python file at agents/report_generator.py.

Implement run_report_generator(player_name: str, scout_output: dict,
                                research_output: dict, comparison_output: dict,
                                session_id: str) -> dict

This agent does NOT use a tool-use loop — it receives structured data 
and writes a report using a single Gemini call.

1. Use REPORT_SYSTEM_PROMPT
2. Use model "gemini-1.5-pro"
3. Build a user prompt that includes:
   - Player name
   - Scout output summary and player stats
   - Research output (market value, injury status, news)
   - Comparison output summary
4. Ask Gemini to write a structured scouting report following the 6-section format
5. Also ask it to output the recommendation as one of: "RECOMMENDED", "CONDITIONAL", "NOT RECOMMENDED"

Return:
{
  "report_markdown": str,  # Full markdown report for UI display
  "recommendation": str,   # "RECOMMENDED" / "CONDITIONAL" / "NOT RECOMMENDED"
  "executive_summary": str,  # First 2-3 sentences only (for card preview)
  "player_name": player_name,
  "session_id": session_id
}
```

---

### `agents/planner.py`

```
Write a Python file at agents/planner.py.

This is the most important file. Implement run_planner(
  user_query: str,
  session_id: str,
  progress_callback = None
) -> dict

The progress_callback is a function(message: str, event_type: str) -> None
that the frontend calls to show the live reasoning trace.
event_type is one of: "plan", "delegate", "result", "error"

Implementation:

1. Use PLANNER_SYSTEM_PROMPT from agents.prompts
2. Use model "gemini-1.5-pro"
3. Import build_context_packet from memory.context
4. Import all run_*_agent functions from their modules

5. AGENT_DISPATCH dict:
   {
     "delegate_to_scout": run_scout_agent,
     "delegate_to_research": run_research_agent,
     "delegate_to_comparison": run_comparison_agent,
     "delegate_to_squad_builder": run_squad_builder_agent,
     "delegate_to_report": run_report_generator,
   }

6. Planner tool definitions (these are NOT player tools, they are delegation tools):
   [
     {"name": "delegate_to_scout", "description": "Search and discover players"},
     {"name": "delegate_to_research", "description": "Get real-time market values, injuries, news"},
     {"name": "delegate_to_comparison", "description": "Compare players statistically"},
     {"name": "delegate_to_squad_builder", "description": "Build formations and squads"},
     {"name": "delegate_to_report", "description": "Generate final scouting report"},
   ]

7. Main loop (max 15 iterations):
   a. Call build_context_packet(session_id, user_query)
   b. Inject context into system prompt
   c. Send query to Gemini with delegation tools
   d. On function_call: 
      - Call progress_callback(f"Delegating to {agent_name}...", "delegate") if provided
      - Look up agent in AGENT_DISPATCH
      - Pass args + context + session_id to the agent
      - Call progress_callback(f"{agent_name} complete", "result") if provided
      - Send function_response back to Gemini
   e. On text response: break

8. After loop:
   - Store trace to MongoDB using store_memory(session_id, "trace", {...})
   - Store the query as a search memory

9. Return:
   {
     "response": final_text,
     "trace": list of reasoning steps,
     "agent_outputs": dict of each agent's output,
     "session_id": session_id
   }

10. Wrap entire function in try/except PlannerTimeoutError
    Raise PlannerTimeoutError if loop hits 15 iterations without text response
```

---

### `agents/debate.py`

```
Write a Python file at agents/debate.py.

Implement agent_debate(player_name: str, session_id: str) -> dict

This runs two scout agents simultaneously with opposing briefs,
then has the planner synthesise both views.

1. Use Python's concurrent.futures.ThreadPoolExecutor to run both agents in parallel:

   pro_future = executor.submit(
     run_scout_agent,
     f"Build the strongest possible case FOR signing {player_name}. 
       Find all positive stats, good form, tactical fit. Be optimistic.",
     session_id + "_pro",
     bias="positive"
   )
   
   con_future = executor.submit(
     run_scout_agent,
     f"Build the strongest possible case AGAINST signing {player_name}. 
       Find injury history, age concerns, overpricing, tactical risks. Be critical.",
     session_id + "_con",
     bias="critical"
   )

2. Wait for both to complete (timeout=60 seconds each)

3. Call run_planner with synthesis query:
   "Given these two perspectives on signing {player_name}:
    PRO: {pro_result['summary']}
    CON: {con_result['summary']}
    Make a final recommendation. Acknowledge both sides explicitly."

4. Return:
   {
     "player_name": player_name,
     "pro_case": pro_result["summary"],
     "con_case": con_result["summary"],
     "verdict": planner_result["response"],
     "recommendation": "RECOMMENDED" / "CONDITIONAL" / "NOT RECOMMENDED"
   }
   
   Parse recommendation from the verdict text — look for the keywords.
```

---

### `memory/feedback.py`

```
Write a Python file at memory/feedback.py.

Implement:

1. record_feedback(session_id: str, player_name: str, 
                    signal: int, reason: str = "") -> dict
   - signal: 1 = positive, -1 = negative/blacklist
   - Finds the player by name to get their _id
   - Stores a feedback memory: 
     content = {"player_id": str(_id), "player_name": player_name, 
                "signal": signal, "reason": reason}
   - Returns {"success": True, "player_name": player_name, 
              "blacklisted": signal == -1}

2. get_user_feedback_summary(session_id: str) -> dict
   - Returns:
     {
       "liked_players": [names where signal == 1],
       "disliked_players": [names where signal == -1],
       "total_feedback": int
     }

3. clear_feedback(session_id: str) -> dict
   - Deletes all feedback memories for the session
   - Returns {"deleted": int}
```

---

### `db/shortlists.py`

```
Write a Python file at db/shortlists.py.

Implement simple CRUD for the shortlists collection:

1. save_shortlist(session_id: str, name: str, player_names: list[str], 
                   notes: str = "") -> dict
   - Upserts (update or insert) a shortlist by session_id + name
   - Returns {"success": True, "name": name, "count": len(player_names)}

2. get_shortlist(session_id: str, name: str) -> dict | None
   - Returns the shortlist document or None

3. get_all_shortlists(session_id: str) -> list[dict]
   - Returns all shortlists for the session with player count

4. delete_shortlist(session_id: str, name: str) -> dict
   - Deletes a shortlist by session_id + name
   - Returns {"deleted": True, "name": name}

5. add_player_to_shortlist(session_id: str, list_name: str, 
                             player_name: str) -> dict
   - Appends a player name to an existing shortlist (or creates it)
   - Returns {"success": True, "total_players": int}
```

---

### `export/pdf_report.py`

```
Write a Python file at export/pdf_report.py.

Use reportlab to generate a professional PDF scouting report.

Implement generate_pdf_report(report_data: dict) -> bytes

report_data will have:
{
  "player_name": str,
  "report_markdown": str,
  "recommendation": str,  # "RECOMMENDED" / "CONDITIONAL" / "NOT RECOMMENDED"
  "executive_summary": str,
  "player_stats": dict,   # from the player document
  "radar_data": dict      # the 0-100 normalised stats
}

PDF layout:
1. Header bar (dark green #0a5c36): "SCOUT AGENT" left, date right, white text
2. Player name as large title (24pt bold)
3. Recommendation badge: green for RECOMMENDED, amber for CONDITIONAL, red for NOT RECOMMENDED
4. Executive Summary section (italic, bordered box)
5. Player Stats table (2 columns: stat name | value)
6. Full report text from report_markdown (parse markdown headers into PDF sections)
7. Footer: "Generated by Scout Agent · Google Agentic AI Hackathon 2026"

Parse the report_markdown by splitting on "## " headers to get sections.
Each section gets a green section header bar and body text.

Return the PDF as bytes so Streamlit can serve it via st.download_button().

Use only reportlab.platypus (SimpleDocTemplate, Paragraph, Table, Spacer) 
and reportlab.lib. No external dependencies.
```

---

### `tests/test_tools.py`

```
Write a Python file at tests/test_tools.py using pytest.

Write tests for the core tool functions. 
Use pytest fixtures and mock MongoDB calls where needed (use unittest.mock).

Tests to write:

1. test_search_players_returns_list
   - Call search_players(position="FWD", top_n=3)
   - Assert result is dict with "players" key
   - Assert len(result["players"]) <= 3

2. test_search_players_position_filter
   - Call search_players(position="GK", top_n=5)
   - Assert all returned players have position containing "GK"

3. test_compare_players_returns_radar_data
   - Call compare_players("player_a_name", "player_b_name")
   - If both players exist: assert "radar_data" in result
   - If player not found: assert "error" in result

4. test_build_player_stat_string
   - Create a mock player dict
   - Call build_player_stat_string(player)
   - Assert result is a non-empty string
   - Assert "position" in result

5. test_tool_registry_has_all_tools
   - Import TOOL_REGISTRY
   - Assert all expected tool names are keys in TOOL_REGISTRY

Run with: pytest tests/test_tools.py -v
```

---

### `tests/test_memory.py`

```
Write a Python file at tests/test_memory.py using pytest.

Tests for the memory system.

1. test_store_and_retrieve_preference
   - Call store_memory("test_session", "preference", 
     {"club_name": "Arsenal", "budget_eur": 80000000, 
      "tactical_style": "high_press", "formation_pref": "4-3-3",
      "priority_positions": ["RW", "CDM"]})
   - Call get_preferences("test_session")
   - Assert result is not None
   - Assert result["club_name"] == "Arsenal"

2. test_blacklist_feedback
   - Call store_memory("test_session", "feedback",
     {"player_id": "test_id_123", "player_name": "Test Player",
      "signal": -1, "reason": "too expensive"})
   - Call get_blacklisted_players("test_session")
   - Assert "test_id_123" in result

3. test_build_context_packet_returns_structure
   - Call build_context_packet("test_session", "find a striker")
   - Assert result is a dict
   - Assert "session_id" in result
   - Assert "club_profile" in result
   - Assert "blacklisted_player_ids" in result
   - Assert "recent_searches" in result

4. test_embed_text_returns_list
   - Call embed_text("position:FWD goals:18 assists:14")
   - Assert result is a list
   - Assert len(result) == 768

5. test_record_feedback
   - Call record_feedback("test_session", "Test Player", signal=-1, reason="too old")
   - Assert result["success"] == True
   - Assert result["blacklisted"] == True

Clean up test data after each test using a pytest fixture that calls 
delete_memories("test_session") in teardown.

Skip tests that require Gemini API if GEMINI_API_KEY not set.
```

---

### `tests/test_queries.py`

```
Write a Python file at tests/test_queries.py using pytest.

Tests for the database query layer.

1. test_get_all_leagues_returns_list
   - Call get_all_leagues()
   - Assert result is a list
   - Assert len(result) > 0
   - Assert all items are strings

2. test_get_all_nationalities_returns_list
   - Call get_all_nationalities()
   - Assert result is a list
   - Assert len(result) > 0

3. test_count_players_nonzero
   - Call count_players()
   - Assert result > 0
   - Print the count so we can verify data loaded correctly

4. test_get_players_by_position
   - Call get_players_by_position("GK", limit=5)
   - Assert result is a list
   - Assert len(result) <= 5

5. test_get_player_by_name_known
   - Call get_player_by_name("Mbappe") (or any player likely in EAFC 26)
   - If result is not None: assert "name" in result and "position" in result
   - If result is None: skip with pytest.skip("Player not in dataset")

6. test_shortlist_crud
   - Call save_shortlist("test_session", "My List", ["Player A", "Player B"])
   - Call get_shortlist("test_session", "My List")
   - Assert result is not None
   - Assert len(result["player_names"]) == 2
   - Call delete_shortlist("test_session", "My List")
   - Assert get_shortlist("test_session", "My List") is None

These tests require a live MongoDB connection with data loaded.
Skip all tests if MONGODB_URI not set in environment.
```

---

### `tests/test_agents.py`

```
Write a Python file at tests/test_agents.py using pytest.

Integration tests for the agent loop. 
These tests make real Gemini API calls — mark them with @pytest.mark.integration

Tests:

1. test_scout_agent_basic
   - Call run_scout_agent("Find a striker from Brazil", "test_session")
   - Assert result has "summary" key (non-empty string)
   - Assert result has "tool_calls" key (list, at least 1 call)

2. test_scout_agent_returns_players
   - Call run_scout_agent("Find top 3 left wingers", "test_session")  
   - Assert result["players"] is a list

3. test_planner_delegates
   - Call run_planner("Find a young midfielder from Spain", "test_session")
   - Assert result has "response" key
   - Assert result has "trace" key (list, at least 1 entry)
   - Assert result["trace"][0] has "agent" key

Skip integration tests in CI if GEMINI_API_KEY not set:
  pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"), 
    reason="GEMINI_API_KEY not set"
  )
```

---

## Interface Contract With Frontend Teammate

These are the exact function signatures your teammate depends on. Do not change them.

```python
# 1. Main query endpoint — frontend calls this on every user message
from agents.planner import run_planner
result = run_planner(
    user_query="Find a Salah replacement under €60M",
    session_id="user_arsenal",
    progress_callback=lambda msg, event: st.session_state.trace.append(msg)
)
# result: {"response": str, "trace": list, "agent_outputs": dict}

# 2. Radar chart data — frontend passes directly to plotly
from tools.comparison_tools import compare_players
result = compare_players("Player A", "Player B")
# result["radar_data"]: {"player_a": {"pace": 0-100, ...}, "player_b": {...}}

# 3. PDF export — frontend passes to st.download_button
from export.pdf_report import generate_pdf_report
pdf_bytes = generate_pdf_report(report_data)
# pdf_bytes: bytes

# 4. Feedback — frontend calls on thumbs up/down
from memory.feedback import record_feedback
record_feedback(session_id, player_name, signal=1 or -1, reason="too expensive")

# 5. Agent debate — frontend calls on debate button click
from agents.debate import agent_debate
result = agent_debate(player_name, session_id)
# result: {"pro_case": str, "con_case": str, "verdict": str, "recommendation": str}

# 6. Shortlists — frontend calls on save button
from db.shortlists import save_shortlist, get_all_shortlists
save_shortlist(session_id, "Main shortlist", ["Lamine Yamal", "Vinicius Jr"])
```

---

## Demo Test — Run This Before Submission

Run in order to verify the entire pipeline works:

```bash
# 1. Verify DB connection
python -c "from db.connection import get_collection; print('DB OK:', get_collection('players').count_documents({}))"

# 2. Verify data loaded
python -c "from tools.player_tools import search_players; import json; print(json.dumps(search_players(position='FWD', top_n=2), indent=2))"

# 3. Verify vector search
python -c "from tools.player_tools import player_similarity_search; print(player_similarity_search('Kylian Mbappe', top_n=3))"

# 4. Verify full planner
python -c "
from agents.planner import run_planner
result = run_planner('Find a young striker from Brazil under 25', 'demo_test')
print('Response:', result['response'][:200])
print('Trace steps:', len(result['trace']))
"

# 5. Verify debate
python -c "
from agents.debate import agent_debate
result = agent_debate('Lamine Yamal', 'demo_test')
print('Verdict:', result['verdict'][:200])
"
```

All 5 should run without errors before you submit.

---

## Common Issues and Fixes

| Issue | Likely Cause | Fix |
| --- | --- | --- |
| `MongoServerError: bad auth` | Wrong URI in .env | Re-copy URI from Atlas → Connect |
| `$vectorSearch` pipeline fails | Vector index not created yet | Create index in Atlas UI first |
| Gemini returns no function_call | Tool definitions malformed | Print `response.parts` to debug |
| `stats_embedding` is `[]` | `compute_embeddings.py` not run | Run `python -m data.compute_embeddings` |
| External API 403 errors | Missing API keys | Add RAPIDAPI_KEY and NEWSAPI_KEY to .env |
| Planner hits 15 iterations | Query too complex or tools failing | Check tool_registry has all tools registered |
| CSV column not found | EAFC 26 columns differ | Run `df.columns.tolist()` and update mapping |

---

*Scout Agent · Google Agentic AI Hackathon 2026 · Good luck Savya.*