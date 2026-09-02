"""Runtime governance controls."""
MAX_QUERY_CHARS = 4000
def within_request_budget(query: str) -> bool:
    """A deterministic proxy cap for per-request token/cost consumption."""
    return len(query) <= MAX_QUERY_CHARS
