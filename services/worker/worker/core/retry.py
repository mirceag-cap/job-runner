import random


def compute_backoff_seconds(attempts: int, base: int, cap: int, jitter_ratio: float = 0.3) -> int:
    raw = base * (2 ** (attempts -1))
    raw_capped = min(raw, cap)

    jitter_amount = raw_capped * jitter_ratio
    low = raw_capped - jitter_amount
    high = raw_capped + jitter_amount

    jittered = random.uniform(low, high)
    return max(0, int(round(jittered)))