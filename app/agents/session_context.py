from app.agents.state import Agentstate


def format_session_context(state: Agentstate) -> str:
    parts = []
    if state.get("account_id"):
        parts.append(f"account_id={state['account_id']}")
    if state.get("case_id"):
        parts.append(f"case_id={state['case_id']}")
    if state.get("user_id"):
        parts.append(f"user_id={state['user_id']}")
    if state.get("card_last4"):
        parts.append(f"card_last4={state['card_last4']}")
    if state.get("txn_id"):
        parts.append(f"txn_id={state['txn_id']}")
    if not parts:
        return "No IDs stored yet for this conversation."
    return "Known session IDs (reuse for follow-ups like 'my card', 'block it'): " + ", ".join(parts)
