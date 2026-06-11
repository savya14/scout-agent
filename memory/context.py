from db.memories import get_preferences, get_blacklisted_players, get_recent_searches, store_memory


def build_context_packet(session_id: str, query: str = "") -> dict:
    """Build a context packet injected into every agent call."""
    preferences = get_preferences(session_id) or {}
    blacklisted = get_blacklisted_players(session_id)
    recent = get_recent_searches(session_id)

    # Store this search in memory
    if query:
        store_memory(session_id, "search", {"query": query})

    return {
        "session_id": session_id,
        "query": query,
        "club_profile": preferences,
        "blacklisted_player_ids": blacklisted,
        "recent_searches": [r.get("query", "") for r in recent],
    }


def format_context_for_prompt(context: dict) -> str:
    """Format context packet as readable text for agent prompts."""
    lines = []

    if context.get("club_profile"):
        p = context["club_profile"]
        lines.append(f"Club Profile: {p.get('club_name', 'Unknown')} | "
                     f"Budget: €{p.get('budget_eur', 'N/A')} | "
                     f"Style: {p.get('tactical_style', 'N/A')} | "
                     f"Formation: {p.get('formation_pref', 'N/A')}")

    if context.get("blacklisted_player_ids"):
        lines.append(f"Blacklisted players (do not recommend): "
                     f"{len(context['blacklisted_player_ids'])} players excluded")

    if context.get("recent_searches"):
        lines.append(f"Recent searches: {', '.join(context['recent_searches'][-3:])}")

    return "\n".join(lines) if lines else "No prior context."