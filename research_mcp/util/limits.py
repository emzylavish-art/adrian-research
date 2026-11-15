"""Hard caps shared by appended tools."""


def clamp_count(count, default: int = 10, lo: int = 1, hi: int = 50) -> int:
    try:
        number = int(count)
    except (TypeError, ValueError):
        number = default
    return max(lo, min(number, hi))


def default_timeout(kind: str) -> int:
    if kind == "download":
        return 900
    return 60
