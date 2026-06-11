import streamlit as st
from agents.transfer_recommender import run_transfer_recommender
from agents.query_agent_v2 import run_query_agent
from agents.planner import run_planner
from agents.debate import agent_debate
from db.shortlists import (
    save_shortlist, get_all_shortlists,
    add_player_to_shortlist, delete_shortlist
)
from memory.feedback import record_feedback

st.set_page_config(
    page_title="Scout Agent",
    page_icon="⚽",
    layout="wide"
)

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "shortlist" not in st.session_state:
    st.session_state.shortlist = []

SESSION_ID = st.session_state.session_id

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
    <h1 style='text-align: center;'>⚽ Scout Agent</h1>
    <p style='text-align: center; color: #888; font-size: 16px;'>
        AI-powered football scouting platform
    </p>
    <hr>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Player Search",
    "🔄 Transfer Recommender",
    "🤖 Agent Debate",
    "📋 Shortlist",
])


# ─── TAB 1: Natural Language Player Search ────────────────────────────────────
with tab1:
    st.subheader("Natural Language Player Search")
    st.caption("Ask anything — e.g. 'Find young Spanish midfielders under 23 with rating above 82'")

    query = st.text_input(
        "Scout Query",
        placeholder="Find a young Brazilian winger under 22 with rating above 80...",
        key="search_query"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        search_btn = st.button("🔍 Search", use_container_width=True)

    if search_btn and query:
        with st.spinner("Analysing query..."):
            result = run_query_agent(query)

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            filters = result.get("filters", {})
            players = result.get("players", [])

            with st.expander("🔧 Extracted Filters", expanded=False):
                cols = st.columns(4)
                filter_items = {k: v for k, v in filters.items() if v is not None}
                for i, (k, v) in enumerate(filter_items.items()):
                    cols[i % 4].metric(k.replace("_", " ").title(), v)

            st.markdown(f"**{len(players)} players found**")

            if not players:
                st.warning("No players found. Try broadening your search criteria.")
            else:
                for p in players:
                    with st.container():
                        c1, c2, c3, c4, c5, c6 = st.columns([3, 1, 1, 1, 2, 1])
                        with c1:
                            st.markdown(f"**{p.get('name', 'N/A')}**")
                            st.caption(f"{p.get('club_name', '')} · {p.get('league_name', '')}")
                        with c2:
                            st.metric("OVR", p.get("overall_rating", "-"))
                        with c3:
                            st.metric("Age", p.get("age", "-"))
                        with c4:
                            st.metric("Position", p.get("position", "-"))
                        with c5:
                            st.caption(p.get("nationality", ""))
                        with c6:
                            if st.button("+ List", key=f"add_{p.get('name')}"):
                                name = p.get("name", "")
                                if name not in st.session_state.shortlist:
                                    st.session_state.shortlist.append(name)
                                    add_player_to_shortlist(SESSION_ID, "My Shortlist", name)
                                    st.success(f"Added {name}")

                        stat_cols = st.columns(6)
                        for j, (stat, key) in enumerate([
                            ("PAC", "pace"), ("SHO", "shooting"), ("PAS", "passing"),
                            ("DRI", "dribbling"), ("DEF", "defending"), ("PHY", "physic")
                        ]):
                            stat_cols[j].metric(stat, p.get(key, 0))

                        # Feedback
                        fb1, fb2, _ = st.columns([1, 1, 8])
                        with fb1:
                            if st.button("👍", key=f"up_{p.get('name')}"):
                                record_feedback(SESSION_ID, p.get("name", ""), signal=1)
                                st.toast("Positive feedback saved")
                        with fb2:
                            if st.button("👎", key=f"down_{p.get('name')}"):
                                record_feedback(SESSION_ID, p.get("name", ""), signal=-1)
                                st.toast("Player blacklisted for this session")

                        st.divider()

    elif search_btn and not query:
        st.warning("Please enter a search query.")


# ─── TAB 2: Transfer Recommender ─────────────────────────────────────────────
with tab2:
    st.subheader("Transfer Recommender")
    st.caption("Enter a player name to find the best replacement candidates")

    player_input = st.text_input(
        "Player to Replace",
        placeholder="e.g. Pedri, Vinicius, Haaland...",
        key="transfer_input"
    )

    recommend_btn = st.button("🔄 Find Replacements", use_container_width=False)

    if recommend_btn and player_input:
        with st.spinner(f"Scouting replacements for {player_input}..."):
            result = run_transfer_recommender(player_input, return_data=True)

        if not result:
            st.error(f"❌ Player '{player_input}' not found.")
        elif "error" in result:
            st.warning(f"⚠️ {result['error']}")
        else:
            player = result["player"]
            candidates = result["candidates"]
            report = result["report"]

            st.markdown("### Player Being Replaced")
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Name", player.get("name", "N/A"))
            m2.metric("Club", player.get("club_name", "N/A"))
            m3.metric("OVR", player.get("overall_rating", "-"))
            m4.metric("Age", player.get("age", "-"))
            m5.metric("Position", player.get("position", "-"))
            m6.metric("Nationality", player.get("nationality", "-"))

            st.divider()

            st.markdown("#### Attribute Breakdown")
            stat_cols = st.columns(6)
            for i, (stat, key) in enumerate([
                ("PAC", "pace"), ("SHO", "shooting"), ("PAS", "passing"),
                ("DRI", "dribbling"), ("DEF", "defending"), ("PHY", "physic")
            ]):
                stat_cols[i].metric(stat, player.get(key, 0))

            st.divider()

            with st.expander(f"📋 {len(candidates)} Candidates Analysed", expanded=False):
                for p in candidates:
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(
                            f"**{p.get('name')}** — "
                            f"{p.get('club_name')} · OVR {p.get('overall_rating')} · Age {p.get('age')}"
                        )
                    with col_b:
                        if st.button("+ List", key=f"tr_add_{p.get('name')}"):
                            name = p.get("name", "")
                            if name not in st.session_state.shortlist:
                                st.session_state.shortlist.append(name)
                                add_player_to_shortlist(SESSION_ID, "My Shortlist", name)
                                st.success(f"Added {name}")

            st.markdown("### Transfer Recommendation Report")
            st.markdown(
                f"<div style='"
                f"background: #0f1117; color: #e8e8e8; padding: 1.5rem 2rem; "
                f"border-radius: 10px; border-left: 4px solid #00c853; "
                f"white-space: pre-wrap; font-family: monospace; "
                f"font-size: 13px; line-height: 1.7;'>"
                f"{report}</div>",
                unsafe_allow_html=True
            )

    elif recommend_btn and not player_input:
        st.warning("Please enter a player name.")


# ─── TAB 3: Agent Debate ─────────────────────────────────────────────────────
with tab3:
    st.subheader("Agent Debate")
    st.caption("Two AI scouts debate whether to sign a player. The Head of Scouting gives the verdict.")

    debate_input = st.text_input(
        "Player to Debate",
        placeholder="e.g. Lamine Yamal, Bellingham, Haaland...",
        key="debate_input"
    )

    debate_btn = st.button("⚔️ Start Debate", use_container_width=False)

    if debate_btn and debate_input:
        with st.spinner(f"Scouts are debating {debate_input}..."):
            result = agent_debate(debate_input, session_id=SESSION_ID)

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            player = result["player"]

            # Player header
            st.markdown(f"### Debate: Should we sign {player.get('name')}?")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Club", player.get("club_name", "-"))
            m2.metric("OVR", player.get("overall_rating", "-"))
            m3.metric("Age", player.get("age", "-"))
            m4.metric("Position", player.get("position", "-"))

            st.divider()

            # Two columns for pro/con
            col_pro, col_con = st.columns(2)

            with col_pro:
                st.markdown("#### 🟢 Scout A — Sign Him")
                st.markdown(
                    f"<div style='background:#0a2e1a; padding:1rem; border-radius:8px; "
                    f"border-left:4px solid #00c853; color:#e8e8e8; "
                    f"font-size:14px; line-height:1.7;'>"
                    f"{result['pro_case']}</div>",
                    unsafe_allow_html=True
                )

            with col_con:
                st.markdown("#### 🔴 Scout B — Don't Sign")
                st.markdown(
                    f"<div style='background:#2e0a0a; padding:1rem; border-radius:8px; "
                    f"border-left:4px solid #ff1744; color:#e8e8e8; "
                    f"font-size:14px; line-height:1.7;'>"
                    f"{result['con_case']}</div>",
                    unsafe_allow_html=True
                )

            st.divider()

            # Verdict
            rec = result["recommendation"]
            rec_color = {"SIGN": "#00c853", "DO NOT SIGN": "#ff1744", "MONITOR": "#ff9800"}.get(rec, "#888")
            rec_emoji = {"SIGN": "✅", "DO NOT SIGN": "❌", "MONITOR": "👁️"}.get(rec, "❓")

            st.markdown(f"### Head of Scouting Verdict")
            st.markdown(
                f"<div style='text-align:center; font-size:2rem; font-weight:bold; "
                f"color:{rec_color}; padding:1rem;'>"
                f"{rec_emoji} {rec}</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='background:#0f1117; padding:1.5rem; border-radius:8px; "
                f"border-left:4px solid {rec_color}; color:#e8e8e8; "
                f"font-size:14px; line-height:1.7;'>"
                f"{result['verdict']}</div>",
                unsafe_allow_html=True
            )

            # Add to shortlist button
            st.divider()
            if rec == "SIGN":
                if st.button(f"+ Add {player.get('name')} to Shortlist"):
                    name = player.get("name", "")
                    if name not in st.session_state.shortlist:
                        st.session_state.shortlist.append(name)
                        add_player_to_shortlist(SESSION_ID, "My Shortlist", name)
                    st.success(f"Added {name} to shortlist!")

    elif debate_btn and not debate_input:
        st.warning("Please enter a player name.")


# ─── TAB 4: Shortlist ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("My Shortlist")
    st.caption("Players you've saved across the platform")

    # Load from DB
    db_lists = get_all_shortlists(SESSION_ID)
    all_players = []
    for sl in db_lists:
        all_players.extend(sl.get("player_names", []))
    # Deduplicate preserving order
    seen = set()
    unique_players = []
    for p in all_players:
        if p not in seen:
            seen.add(p)
            unique_players.append(p)

    if not unique_players:
        st.info("No players shortlisted yet. Use the + List buttons in Player Search or Transfer Recommender.")
    else:
        st.markdown(f"**{len(unique_players)} players shortlisted**")
        st.divider()

        for player_name in unique_players:
            col_name, col_remove = st.columns([5, 1])
            with col_name:
                st.markdown(f"⚽ **{player_name}**")
            with col_remove:
                if st.button("Remove", key=f"rm_{player_name}"):
                    from db.shortlists import remove_player_from_shortlist
                    remove_player_from_shortlist(SESSION_ID, "My Shortlist", player_name)
                    if player_name in st.session_state.shortlist:
                        st.session_state.shortlist.remove(player_name)
                    st.rerun()

        st.divider()

        # Save named shortlist
        st.markdown("#### Save as Named Shortlist")
        col_name_input, col_save = st.columns([3, 1])
        with col_name_input:
            list_name = st.text_input("Shortlist Name", value="My Shortlist", key="list_name")
        with col_save:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Save", use_container_width=True):
                save_shortlist(SESSION_ID, list_name, unique_players)
                st.success(f"Saved '{list_name}' with {len(unique_players)} players!")

        # Clear all
        if st.button("🗑️ Clear Shortlist"):
            delete_shortlist(SESSION_ID, "My Shortlist")
            st.session_state.shortlist = []
            st.rerun()