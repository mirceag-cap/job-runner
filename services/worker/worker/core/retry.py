def compute_backoff_seconds(attempts: int, base: int, cap: int) -> int:
    raw = base * (2 ** (attempts -1))
    return min(raw, cap)