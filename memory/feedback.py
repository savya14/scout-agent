from db.memories import store_memory, get_blacklisted_players


def record_feedback(session_id: str, player_name: str, signal: int, reason: str = "") -> dict:
    """
    Record thumbs up (+1) or thumbs down (-1) feedback for a player.
    Negative signal blacklists the player for this session.
    """
    player_id = player_name.lower().replace(" ", "_")

    store_memory(session_id, "feedback", {
        "player_id": player_id,
        "player_name": player_name,
        "signal": signal,
        "reason": reason,
    })

    return {
        "success": True,
        "blacklisted": signal == -1,
        "player": player_name,
    }


def is_blacklisted(session_id: str, player_name: str) -> bool:
    player_id = player_name.lower().replace(" ", "_")
    blacklisted = get_blacklisted_players(session_id)
    return player_id in blacklisted