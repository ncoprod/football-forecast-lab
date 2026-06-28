from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.model import DEFAULT_DIXON_COLES_RHO
from football_forecast_lab.settings import REPO_ROOT
from football_forecast_lab.training_data import build_examples, fetch_historical_results, load_historical_results


def main() -> None:
    rows = load_historical_results(fetch_historical_results())
    examples = build_examples(rows, start_year=2000)
    counter = Counter(example.score for example in examples)
    total = sum(counter.values()) or 1
    artifact = {
        "type": "global_score_frequency_and_dixon_coles_config",
        "source": "martj42/international_results results.csv",
        "rows": len(examples),
        "dixon_coles_rho": DEFAULT_DIXON_COLES_RHO,
        "top_scores": [
            {"score": score, "frequency": count, "probability": count / total}
            for score, count in counter.most_common(25)
        ],
        "note": (
            "This artifact is a conservative score-model reference. Live forecasts still fit "
            "match-specific lambdas from market totals and 1X2 odds before applying Dixon-Coles."
        ),
    }
    output = REPO_ROOT / "models" / "score_model_dixon_coles_v1.json"
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {output}")


if __name__ == "__main__":
    main()
