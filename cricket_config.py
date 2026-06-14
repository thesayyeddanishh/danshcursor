"""
Shared format configuration for consolidated cricket dashboards.

Session state:
  st.session_state["cricket_format"] — one of FORMAT_KEYS (set on Home page).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

FORMAT_KEYS: Tuple[str, ...] = (
    "men_t20i",
    "women_t20i",
    "men_odi",
    "women_odi",
    "men_test",
    "men_test_aus",
)

FORMAT_LABELS: Dict[str, str] = {
    "men_t20i": "Men's T20I",
    "women_t20i": "Women's T20I",
    "men_odi": "Men's ODI",
    "women_odi": "Women's ODI",
    "men_test": "Men's Test",
    "men_test_aus": "Men's Test - AUS",
}


@dataclass(frozen=True)
class FormatConfig:
    key: str
    label: str
    is_test: bool
    is_womens: bool
    is_odi: bool
    sidebar_title: str
    sidebar_sub: str


def resolve_format(key: Optional[str]) -> FormatConfig:
    k = (key or "men_t20i").strip()
    if k not in FORMAT_KEYS:
        k = "men_t20i"
    
    # Update this line to include the new key
    is_test = k in ["men_test", "men_test_aus"] 
    is_womens = k.startswith("women_")
    is_odi = k.endswith("_odi")
    
    if is_test:
        # You can differentiate titles here if needed
        title = "Men's (AUS)" if k == "men_test_aus" else "Men's"
        sub = "Red Ball (Test)"
    elif is_womens:
        title, sub = ("Women's", "ODI") if is_odi else ("Women's", "T20I")
    else:
        title, sub = ("Men's", "ODI") if is_odi else ("Men's", "T20I")
    return FormatConfig(
        key=k,
        label=FORMAT_LABELS[k],
        is_test=is_test,
        is_womens=is_womens,
        is_odi=is_odi,
        sidebar_title=title,
        sidebar_sub=sub,
    )


# --- Match phase (Leaderboard & any Over-based filters) ---
# Over column is treated as 0-based over index (consistent with existing T20 filters).

PHASE_ALL = "All"


def match_phase_options(cfg: FormatConfig) -> List[str]:
    if cfg.is_test:
        return [PHASE_ALL]
    if cfg.is_odi:
        return [
            PHASE_ALL,
            "Powerplay (1-10)",
            "Middle (11-40)",
            "Death (41-50)",
        ]
    return [
        PHASE_ALL,
        "Powerplay (1-6)",
        "Middle (7-16)",
        "Death (17-20)",
    ]


def apply_match_phase_filter(df: pd.DataFrame, phase: str, cfg: FormatConfig) -> pd.DataFrame:
    if df is None or df.empty or "Over" not in df.columns:
        return df
    if phase == PHASE_ALL or cfg.is_test:
        return df
    over = pd.to_numeric(df["Over"], errors="coerce")
    d = df.copy()
    d["_over_num"] = over
    d = d.dropna(subset=["_over_num"])
    if cfg.is_odi:
        if phase == "Powerplay (1-6)":
            d = d[d["_over_num"] < 6]
        elif phase == "Middle (7-40)":
            d = d[(d["_over_num"] >= 6) & (d["_over_num"] < 40)]
        elif phase == "Death (41-50)":
            d = d[(d["_over_num"] >= 40) & (d["_over_num"] < 50)]
    else:
        if phase == "Powerplay (1-6)":
            d = d[d["_over_num"] < 6]
        elif phase == "Middle (7-16)":
            d = d[(d["_over_num"] >= 6) & (d["_over_num"] < 16)]
        elif phase == "Death (17-20)":
            d = d[d["_over_num"] >= 16]
    return d.drop(columns=["_over_num"])


# --- Pitch bins (Seam / Spin) for charts ---

def seam_pitch_bins_men_t20() -> Dict[str, List[float]]:
    return {
        "Full Toss": [-4, 0.5],
        "Yorker": [0.5, 2.5],
        "The Slot": [2.5, 5.8],
        "Length": [5.8, 8],
        "Short": [8, 10],
        "Bouncer": [10, 16],
    }


def seam_pitch_bins_women_t20() -> Dict[str, List[float]]:
    # Women's white-ball: short band runs through 16 m (no separate "Bouncer" bucket)
    return {
        "Full Toss": [-5, 0.9],
        "Yorker": [0.9, 2.8],
        "The Slot": [2.8, 5.5],
        "Length": [5.5, 8],
        "Short": [8, 16],
    }


def seam_pitch_bins_test() -> Dict[str, List[float]]:
    return {
        "Full": [-5, 5.8],
        "Length": [5.8, 8],
        "Short": [8, 10],
        "Bouncer": [10, 16],
    }

def seam_pitch_bins_test_aus() -> Dict[str, List[float]]:
    return {
        "Full": [-5, 5],
        "Length": [5, 7],
        "Short": [7, 10],
        "Bouncer": [10, 16],
    }


def spin_pitch_bins_men_t20() -> Dict[str, List[float]]:
    return {
        "OP": [-2, 2.8],
        "Full": [2.8, 4.4],
        "Good": [4.4, 6.2],
        "Short": [6.2, 15.0],
    }


def spin_pitch_bins_women_t20() -> Dict[str, List[float]]:
    return {
        "OP": [-2, 2.5],
        "Full": [2.5, 4],
        "Good": [4, 5.7],
        "Short": [5.7, 12],
    }


def spin_pitch_bins_test() -> Dict[str, List[float]]:
    return {
        "OP": [-2, 2.8],
        "Full": [2.8, 4.4],
        "Good": [4.4, 6.2],
        "Short": [6.2, 15.0],
    }

def get_pitch_bins(delivery_type: str, cfg: FormatConfig) -> Dict[str, List[float]]:
    # --- New Logic for AUS ---
    if cfg.key == "men_test_aus":
        if delivery_type == "Seam":
            return seam_pitch_bins_test_aus()
        if delivery_type == "Spin":
            return spin_pitch_bins_test()
        return {}

    if cfg.is_test:
        if delivery_type == "Seam":
            return seam_pitch_bins_test()
        if delivery_type == "Spin":
            return spin_pitch_bins_test()
        return {}
    if cfg.is_womens:
        if delivery_type == "Seam":
            return seam_pitch_bins_women_t20()
        if delivery_type == "Spin":
            return spin_pitch_bins_women_t20()
        return {}
    if delivery_type == "Seam":
        return seam_pitch_bins_men_t20()
    if delivery_type == "Spin":
        return spin_pitch_bins_men_t20()
    return {}


def ordered_seam_keys(cfg: FormatConfig) -> List[str]:
    if cfg.is_test:
        return ["Full", "Length", "Short", "Bouncer"]
    if cfg.is_womens:
        return ["Full Toss", "Yorker", "The Slot", "Length", "Short"]
    return ["Full Toss", "Yorker", "The Slot", "Length", "Short", "Bouncer"]


def ordered_spin_keys(cfg: FormatConfig) -> List[str]:
    return ["OP", "Full", "Good", "Short"]


# --- Speed buckets (Batters / Pacers charts) ---

def seam_speed_group(speed: float, cfg: FormatConfig) -> str:
    if cfg.is_womens:
        if speed < 105:
            return "<105"
        if 105 <= speed <= 118:
            return "105-118"
        return "118+"
    if speed < 125:
        return "<125"
    if 125 <= speed <= 140:
        return "125-140"
    return "140+"


def seam_speed_ordered_groups(cfg: FormatConfig) -> List[str]:
    if cfg.is_womens:
        return ["118+", "105-118", "<105"]
    return ["140+", "125-140", "<125"]


def spin_speed_group(speed: float, cfg: FormatConfig) -> str:
    if speed < 85:
        return "<85"
    if 85 <= speed <= 95:
        return "85-95"
    return "95+"


def spin_speed_ordered_groups(cfg: FormatConfig) -> List[str]:
    return ["95+", "85-95", "<85"]


def pacer_effectiveness_seam_order(cfg: FormatConfig) -> List[str]:
    """Y-axis order for pacer 3-col speed chart (matches original apps)."""
    if cfg.is_womens:
        return ["<105", "105-118", "118+"]
    return ["<125", "125-140", "140+"]


# --- Leaderboard length / pace thresholds ---

def leaderboard_batter_length_options(cfg: FormatConfig) -> List[str]:
    if cfg.is_test:
        return ["All", "FULL", "LENGTH", "SHORT", "BOUNCER"]
    base = ["All", "FULL TOSS", "YORKER", "THE SLOT", "LENGTH", "SHORT"]
    if cfg.is_womens:
        return base
    return base + ["BOUNCER"]


def leaderboard_batter_pace_options(cfg: FormatConfig) -> Tuple[str, str]:
    if cfg.is_womens:
        return "Above 118", "Below 105"
    return "Above 140", "Below 125"


def leaderboard_pacer_pace_range_labels(cfg: FormatConfig) -> Tuple[str, str]:
    return leaderboard_batter_pace_options(cfg)


def filter_batter_length(df: pd.DataFrame, f3: str, cfg: FormatConfig) -> pd.DataFrame:
    """Leaderboard: seam length bucket for batters (BounceX thresholds)."""
    if f3 == "All":
        return df.copy()
    bx = df["BounceX"]
    if cfg.is_test:
        if f3 == "FULL":
            return df[bx < 5.8].copy()
        if f3 == "LENGTH":
            return df[(bx >= 5.8) & (bx < 8.0)].copy()
        if f3 == "SHORT":
            return df[(bx >= 8.0) & (bx < 10.0)].copy()
        if f3 == "BOUNCER":
            return df[bx >= 10.0].copy()
        return df.copy()

    if cfg.key == "men_test_aus":
        if f3 == "FULL": return df[bx < 5.0].copy()
        if f3 == "LENGTH": return df[(bx >= 5.0) & (bx < 7.0)].copy()
        if f3 == "SHORT": return df[(bx >= 7.0) & (bx < 10.0)].copy()
        if f3 == "BOUNCER": return df[bx >= 10.0].copy()
        return df.copy()
  
    if cfg.is_womens:
        if f3 == "FULL TOSS":
            return df[bx < 0.9].copy()
        if f3 == "YORKER":
            return df[(bx >= 0.9) & (bx < 2.8)].copy()
        if f3 == "THE SLOT":
            return df[(bx >= 2.8) & (bx < 5.5)].copy()
        if f3 == "LENGTH":
            return df[(bx >= 5.5) & (bx < 8.0)].copy()
        if f3 == "SHORT":
            return df[(bx >= 8.0) & (bx < 16.0)].copy()
        return df.copy()
    if f3 == "FULL TOSS":
        return df[bx < 0.5].copy()
    if f3 == "YORKER":
        return df[(bx >= 0.5) & (bx < 2.5)].copy()
    if f3 == "THE SLOT":
        return df[(bx >= 2.5) & (bx < 5.8)].copy()
    if f3 == "LENGTH":
        return df[(bx >= 5.8) & (bx < 8.0)].copy()
    if f3 == "SHORT":
        return df[(bx >= 8.0) & (bx < 10.0)].copy()
    if f3 == "BOUNCER":
        return df[bx >= 10.0].copy()
    return df.copy()


def filter_pacer_length(df: pd.DataFrame, f3: str, cfg: FormatConfig) -> pd.DataFrame:
    """Leaderboard: seam length for pacers (includes All for Test)."""
    if f3 == "All":
        return df.copy()
    bx = df["BounceX"]
    if cfg.is_test:
        return filter_batter_length(df, f3, cfg)
    if cfg.is_womens:
        if f3 == "FULL TOSS":
            return df[bx < 0.9].copy()
        if f3 == "YORKER":
            return df[(bx >= 0.9) & (bx < 2.8)].copy()
        if f3 == "THE SLOT":
            return df[(bx >= 2.8) & (bx < 5.5)].copy()
        if f3 == "LENGTH":
            return df[(bx >= 5.5) & (bx < 8.0)].copy()
        if f3 == "SHORT":
            return df[(bx >= 8.0) & (bx < 16.0)].copy()
        return df.copy()
    if f3 == "FULL TOSS":
        return df[bx < 0.5].copy()
    if f3 == "YORKER":
        return df[(bx >= 0.5) & (bx < 2.5)].copy()
    if f3 == "THE SLOT":
        return df[(bx >= 2.5) & (bx < 5.8)].copy()
    if f3 == "LENGTH":
        return df[(bx >= 5.8) & (bx < 8.0)].copy()
    if f3 == "SHORT":
        return df[(bx >= 8.0) & (bx < 10.0)].copy()
    if f3 == "BOUNCER":
        return df[bx >= 10.0].copy()
    return df.copy()


def filter_batter_pace(df: pd.DataFrame, f3: str, cfg: FormatConfig) -> pd.DataFrame:
    hi, lo = leaderboard_batter_pace_options(cfg)
    rs = df["ReleaseSpeed"]
    if f3 == hi:
        thr = 118 if cfg.is_womens else 140
        return df[rs > thr].copy()
    if f3 == lo:
        thr = 105 if cfg.is_womens else 125
        return df[rs < thr].copy()
    return df.copy()


def filter_pacer_pace(df: pd.DataFrame, f3: str, cfg: FormatConfig) -> pd.DataFrame:
    return filter_batter_pace(df, f3, cfg)


def pacer_view_types(cfg: FormatConfig) -> List[str]:
    if cfg.is_test:
        return [
            "All",
            "Bowling Strike Rate By Length",
            "% by Lengths",
            "Bowling Average by Pace",
            "% Balls by Pace",
        ]
    return ["All", "Economy By Length", "% by Lengths", "Economy by Pace", "% Balls by Pace"]


def batter_sr_or_avg_label(cfg: FormatConfig) -> str:
    return "Avg by Length / Pace" if cfg.is_test else "SR by Length / Pace"


def pacer_length_filter_options(cfg: FormatConfig) -> List[str]:
    if cfg.is_test:
        return ["All", "FULL", "LENGTH", "SHORT", "BOUNCER"]
    base = ["FULL TOSS", "YORKER", "THE SLOT", "LENGTH", "SHORT"]
    if cfg.is_womens:
        return base
    return base + ["BOUNCER"]


def spinner_view_types(cfg: FormatConfig) -> List[str]:
    if cfg.is_test:
        return ["All", "Bowling Strike Rate By Length", "% by Lengths", "% /Turn (TURN)"]
    return ["All", "Economy By Length", "% by Lengths", "% /Turn (TURN)"]
