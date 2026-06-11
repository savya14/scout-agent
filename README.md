# ⚽ Scout Agent

**AI-powered football scouting platform — Google Agentic AI Hackathon · MongoDB Track · June 2026**

Scout Agent is a multi-agent AI system that helps football clubs discover players, analyse transfer targets, and make data-driven scouting decisions — powered by Google Gemini, MongoDB Atlas, and 16,228 players from the EAFC 26 dataset.

---

## 🏗️ Architecture

```
           User Query
               │
               ▼
┌─────────────────────────────────┐
│         Streamlit UI            │
│  4 Tabs: Search · Transfer ·   │
│          Debate · Shortlist     │
└──────────────┬──────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌──────────────────┐
│ Query Agent │  │ Transfer Agent   │
│ (NL → DB)   │  │ (Replacements)   │
└──────┬──────┘  └────────┬─────────┘
       │                  │
       ▼                  ▼
┌──────────────────────────────────┐
│         MongoDB Atlas            │
│  16,228 players · EAFC 26 data  │
└──────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│       Google Gemini API          │
│  NL parsing · Reports · Debate  │
└──────────────────────────────────┘
```

---

## ✨ Features

### 🔍 Natural Language Player Search
Ask in plain English — the Query Agent uses Gemini to extract filters and queries MongoDB.
> *"Find young Spanish midfielders under 24 with rating above 82"*

### 🔄 Transfer Recommender
Enter any player and get AI-generated transfer recommendations with:
- Position-aware candidate scoring
- Detailed scouting report for top 3 replacements
- Strengths, risks, and final ranking

### ⚔️ Agent Debate
The platform's flagship feature — two AI scouts debate whether to sign a player:
- **Scout A** argues FOR signing
- **Scout B** argues AGAINST
- **Head of Scouting** gives the final verdict: SIGN / DO NOT SIGN / MONITOR

### 📋 Shortlist
Save players across all tabs. Persist shortlists to MongoDB with named lists.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| AI / LLM | Google Gemini API (gemini-2.0-flash) |
| Database | MongoDB Atlas |
| Data | EAFC 26 dataset (16,228 players) |
| Backend | Python 3.11+ |
| Memory | MongoDB (memories, shortlists collections) |
| Config | python-dotenv |
| Models | Pydantic |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/scout-agent.git
cd scout-agent
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```
Edit `.env` and fill in your keys:
```
MONGO_URI=mongodb+srv://...
DB_NAME=scout_db
GEMINI_API_KEY=your_key_here
```

### 5. Load player data
```bash
python data/load_data.py
```

### 6. Run the app
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
scout-agent/
│
├── app.py                          # Streamlit UI — 4 tabs
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── query_agent_v2.py           # NL → MongoDB query agent
│   ├── transfer_recommender.py     # Transfer recommendation agent
│   ├── planner.py                  # Orchestration agent
│   ├── debate.py                   # Agent debate (pro/con/verdict)
│   ├── scout_agent.py              # Scout agent
│   └── prompts.py                  # System prompt constants
│
├── db/
│   ├── connection.py               # MongoDB Atlas singleton
│   ├── queries.py                  # Player search + nickname resolution
│   ├── schemas.py                  # Pydantic models
│   ├── shortlists.py               # Shortlist CRUD
│   └── memories.py                 # Memory CRUD
│
├── memory/
│   ├── context.py                  # Session context builder
│   ├── feedback.py                 # Thumbs up/down feedback
│   └── embeddings.py               # Player stat embeddings
│
├── tools/
│   ├── player_search.py
│   ├── compare_players.py
│   ├── top_players.py
│   ├── club_search.py
│   ├── position_search.py
│   └── player_shortlist.py
│
└── data/
    ├── load_data.py                # Ingestion script
    └── EAFC26-Men.csv              # 16,228 players
```

---

## 🗄️ Database Schema

### `players` collection
```json
{
  "name": "Pedri",
  "name_normalized": "pedri",
  "overall_rating": 89,
  "age": 23,
  "position": "CM",
  "club_name": "FC Barcelona",
  "league_name": "LALIGA EA SPORTS",
  "nationality": "Spain",
  "pace": 77, "shooting": 73, "passing": 85,
  "dribbling": 91, "defending": 78, "physic": 77
}
```

---

## 🎯 Hackathon Highlights

- **Multi-agent architecture** — Query Agent, Transfer Agent, Planner Agent, Debate Agents all running independently
- **Agent Debate** — novel feature where two AI agents argue opposite positions before a third gives a verdict
- **Persistent memory** — MongoDB stores session context, feedback, and shortlists across queries
- **Position-aware scoring** — custom composite scoring weights per position (ST, CM, CB, GK etc.)
- **Nickname resolution** — handles "Mbappe", "CR7", "Vinicius", "De Bruyne" → resolves to exact DB names

---

## 👥 Team

Built for the **Google Agentic AI Hackathon — MongoDB Partner Track** · June 2026

---

## 📄 License

MIT
