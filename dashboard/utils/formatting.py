# dashboard/utils/formatting.py
#
# Small shared number/percent formatting helpers so metrics look
# consistent across all three pages.

def fmt_pct(value: float, decimals: int = 2) -> str:
    if value is None or value != value:  # NaN check without importing numpy/pandas
        return "\u2013"
    return f"{value:.{decimals}f}%"


def fmt_count(value: int) -> str:
    return f"{value:,}"
