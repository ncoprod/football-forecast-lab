from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs"
CACHE_DIR = REPO_ROOT / ".cache" / "football_forecast_lab"
OUTPUT_DIR = REPO_ROOT / "outputs"

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
ELO_BASE = "https://www.eloratings.net"

GROUP_SCOREBOARD_URL = f"{ESPN_BASE}/scoreboard?dates=20260611-20260627&limit=300"
R32_SCOREBOARD_URL = f"{ESPN_BASE}/scoreboard?dates=20260628-20260704&limit=300"
KNOCKOUT_SCOREBOARD_URL = f"{ESPN_BASE}/scoreboard?dates=20260704-20260719&limit=300"
NEWS_URL = f"{ESPN_BASE}/news?limit=80"

PARIS_TZ = ZoneInfo("Europe/Paris")
USER_AGENT = "Codex football analyst/1.0 (+local personal use)"

DEFAULT_CONFIG = {
    "extra_time_goal_factor": 0.30,
}

TEAM_ALIASES = {
    "USA": "United States",
    "United States": "United States",
    "Congo DR": "DR Congo",
    "Democratic Republic of Congo": "DR Congo",
    "DR Congo": "DR Congo",
    "Cape Verde Islands": "Cape Verde",
    "Cape Verde": "Cape Verde",
    "Cabo Verde": "Cape Verde",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "Ivory Coast": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Netherlands": "Netherlands",
    "South Korea": "South Korea",
}

INJURY_TERMS = (
    "injury",
    "injured",
    "doubt",
    "doubtful",
    "ruled out",
    "suspended",
    "suspension",
    "fitness",
    "hamstring",
    "ankle",
    "knee",
)

def load_config() -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    for path in (CONFIG_DIR / "default.json", CONFIG_DIR / "local.json"):
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            user_config = json.load(f)
        for key, value in user_config.items():
            if key in config and isinstance(value, (int, float)):
                config[key] = float(value)
    return config

