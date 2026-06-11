# ScoutAgent Pro — Frontend Implementation

> Professional multi-agent football scouting platform.  
> Built with Streamlit + Plotly. Agent-first, dashboard-native UI.

---

## Quick Start

```bash
# 1. Install dependencies
pip install streamlit plotly pandas requests

# 2. Run the app
streamlit run app.py
```

The app runs entirely on **mock data** — no backend required for the demo.

---

## File Structure

```
frontend/
├── app.py                          # Main entry point — CSS injection, routing, sidebar
│
├── styles/
│   └── styles.css                  # Complete dark analytics theme (all tokens + components)
│
├── state/
│   └── session_state.py            # All session_state keys — init + helpers
│
├── services/
│   ├── mock_data.py                # Full mock data service (mirrors backend schemas exactly)
│   └── api_client.py               # Real HTTP client (swap in when backend ready)
│
├── pages/
│   ├── dashboard.py                # Dashboard — KPIs, agent feed, recent scouts
│   ├── scout.py                    # Scout — search, filters, player grid, agent panel
│   ├── compare.py                  # Compare — radar chart, stat bars, AI insight
│   ├── transfer_strategy.py        # Transfer Strategy — animated planning + ranked targets ★
│   ├── squad_builder.py            # Squad Builder — formation grid, budget, chemistry
│   ├── shortlists.py               # Shortlists — saved players, export
│   ├── memory_center.py            # Memory Center — club profile, memories, reasoning
│   ├── agent_activity.py           # Agent Activity — LangSmith-style execution traces
│   └── settings.py                 # Settings — API config, system status
│
├── components/
│   └── agent_reasoning_panel.py    # Reusable: AgentReasoningPanel, ExecutionTimeline
│
└── visualizations/
    └── radar_chart.py              # All Plotly chart functions (radar, bar, gauge, donut)
```

---

## Design System

### Colours
| Token        | Hex       | Usage                          |
|-------------|-----------|--------------------------------|
| `--green`   | `#00E87D` | Primary accent, match scores   |
| `--amber`   | `#FF8C00` | Budget, warnings, alerts       |
| `--blue`    | `#3B8EFF` | Secondary data, tool badges    |
| `--purple`  | `#B87DFF` | Agent/AI reasoning             |
| `--red`     | `#FF4545` | Vacancies, high urgency        |
| `--bg`      | `#05080F` | Page background                |
| `--s2`      | `#0D1525` | Card surface                   |

### Typography
- **Syne** — display headings, big numbers, brand
- **DM Sans** — body text, UI labels
- **JetBrains Mono** — agent traces, tool calls, code

---

## Agent Visibility Architecture

The agent is visible **everywhere**, never hidden in a chat box:

| Location | What's shown |
|----------|-------------|
| **Top bar** | Live "Agent Running — Step X/7" pill |
| **Bottom bar** | Agent status + scrolling log + agent dot matrix |
| **Sidebar** | Green pulse dot next to Agent Activity when running |
| **Dashboard** | Full execution step panel with tool outputs |
| **Scout page** | Left panel shows live agent reasoning steps |
| **Transfer Strategy** | Animated planning trace — one step reveals at a time |
| **Agent Activity** | Full LangSmith-style trace with connector lines |

---

## Swapping Mock → Real Backend

Every page imports from `MockDataService`. To connect to the live backend:

```python
# Before (mock):
from services.mock_data import MockDataService as DataService

# After (live):
from services.api_client import APIClient as DataService
```

The `APIClient` mirrors `MockDataService` method signatures exactly.  
Set the API URL in **Settings** or via `st.session_state.settings_api_url`.

---

## Page-by-Page Implementation Notes

### Dashboard (`pages/dashboard.py`)
- 4 KPI cards with colour-coded top border
- Agent activity feed with left-border colour coding
- Position demand horizontal bar chart (Plotly)
- Live agent execution panel — shows steps as they complete

### Scout (`pages/scout.py`)
- 3-column layout: Filters | Player Grid | Detail/Shortlist
- Agent reasoning panel in the left filter column
- Player cards with mini stat bars + radar preview
- Shortlist toggle with session state persistence

### Compare (`pages/compare.py`)
- Player selector buttons for A/B swap
- Dual radar chart with `Scatterpolar` traces
- Head-to-head stat bars (custom HTML)
- Similarity gauge + AI agent verdict panel

### Transfer Strategy (`pages/transfer_strategy.py`) ★ WOW
- Left input panel with Streamlit form widgets
- `time.sleep()` loop reveals agent steps progressively
- Ranked target cards with fit bar + urgency/budget badges
- Budget donut chart + alternative scenarios

### Agent Activity (`pages/agent_activity.py`)
- LangSmith-style vertical trace with connector lines
- Each step: badge → mono call → description → JSON output
- Side panel: agent timing, tool call list, memory operations
- Run ID + aggregate stats header

### Memory Center (`pages/memory_center.py`)
- Club profile card with formation/budget metadata
- Memory card timeline with type icons + colour coding
- Tabbed layout: Memory Store | Search History | Reasoning
- Reasoning history shown as Q&A with confidence scores

### Squad Builder (`pages/squad_builder.py`)
- Dark green pitch background with CSS overlay lines
- Formation slots rendered as flexbox circles
- Vacancies animate with amber glow
- Squad chemistry dual radar (current vs. post-transfer)
- Agent weakness analysis cards

---

## Dependencies

```txt
streamlit>=1.35.0
plotly>=5.20.0
pandas>=2.0.0
requests>=2.31.0
```

---

## Implementation Order (Recommended)

1. `app.py` + `styles/styles.css` + `state/session_state.py` — scaffold
2. `services/mock_data.py` — data layer
3. `pages/dashboard.py` — first visible page
4. `pages/scout.py` — core functionality
5. `pages/transfer_strategy.py` — hackathon WOW feature
6. `pages/agent_activity.py` — judges love this
7. `pages/compare.py` + `pages/memory_center.py`
8. `pages/squad_builder.py` + `pages/shortlists.py`
9. Polish: animations, responsive tweaks, settings

---

*ScoutAgent Pro — Built for the hackathon. Looks like a startup.*
