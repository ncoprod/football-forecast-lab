from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs"
DOCS_DIR = REPO_ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
GENERATED_DIR = DOCS_DIR / "generated"
README_PATH = REPO_ROOT / "README.md"

AUDIT_PATH = OUTPUT_DIR / "match_predictions_2026_r32_audit.json"
ML_RESULT_PATH = OUTPUT_DIR / "ml_training_result.json"
ML_REPORT_PATH = OUTPUT_DIR / "ml_training_report.md"


def main() -> None:
    audit = read_json(AUDIT_PATH)
    ml_result = read_json(ML_RESULT_PATH)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    write_exact_score_chart(audit, ASSETS_DIR / "exact_score_probabilities.svg")
    write_champion_chart(audit, ASSETS_DIR / "champion_probabilities.svg")
    write_backtest_chart(ml_result, ASSETS_DIR / "ml_backtest_log_loss.svg")
    write_latest_results_doc(audit, ml_result, GENERATED_DIR / "latest_results.md")
    publish_csv_outputs()
    update_readme_snapshot(audit, ml_result)
    print("OK: README assets and public snapshots generated.")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def publish_csv_outputs() -> None:
    for name in (
        "match_predictions_2026_r32.csv",
        "champion_simulation_2026.csv",
        "feature_store_current_matches.csv",
        "ml_training_report.md",
    ):
        src = OUTPUT_DIR / name
        if src.exists():
            shutil.copyfile(src, GENERATED_DIR / name)
    for name in ("rolling_origin_report.md", "calibration_report.md"):
        src = OUTPUT_DIR / "backtests" / name
        if src.exists():
            shutil.copyfile(src, GENERATED_DIR / name)


def write_exact_score_chart(audit: dict[str, Any], path: Path) -> None:
    items = [
        (
            short_label(pred["match"], 30),
            float(pred["recommended_exact_probability_90"]),
            f"{pred['recommended_score_90']} - {pct(pred['recommended_exact_probability_90'])}",
        )
        for pred in audit["predictions"]
    ]
    path.write_text(
        horizontal_bar_svg(
            title="Exact score probability by match",
            subtitle="Top predicted final score before penalties",
            items=items,
            color="#2563eb",
            scale_to_max=True,
            width=980,
        ),
        encoding="utf-8",
    )


def write_champion_chart(audit: dict[str, Any], path: Path) -> None:
    advancement = audit["tournament"]["advancement"]
    items = [
        (
            item["team"],
            float(advancement[item["team"]]["champion"]),
            pct(advancement[item["team"]]["champion"]),
        )
        for item in audit["tournament"]["champion_top"][:10]
    ]
    path.write_text(
        horizontal_bar_svg(
            title="Tournament winner simulation",
            subtitle="Champion probability from bracket propagation",
            items=items,
            color="#059669",
            scale_to_max=True,
            width=900,
        ),
        encoding="utf-8",
    )


def write_backtest_chart(ml_result: dict[str, Any], path: Path) -> None:
    metrics = ml_result["test_metrics"]
    baselines = ml_result["test_baselines"]
    items = [
        ("Softmax ML", float(metrics["log_loss"]), f"log loss {metrics['log_loss']:.3f}"),
        ("Elo baseline", float(baselines["elo_baseline"]["log_loss"]), f"log loss {baselines['elo_baseline']['log_loss']:.3f}"),
        ("Majority baseline", float(baselines["majority"]["log_loss"]), f"log loss {baselines['majority']['log_loss']:.3f}"),
    ]
    path.write_text(
        horizontal_bar_svg(
            title="Historical test backtest",
            subtitle="Lower log loss is better",
            items=items,
            color="#7c3aed",
            scale_to_max=True,
            width=900,
        ),
        encoding="utf-8",
    )


def horizontal_bar_svg(
    title: str,
    subtitle: str,
    items: list[tuple[str, float, str]],
    color: str,
    scale_to_max: bool,
    width: int,
) -> str:
    row_height = 34
    top = 84
    left = 235
    right = 150
    bar_width = width - left - right
    height = top + len(items) * row_height + 34
    max_value = max((value for _, value, _ in items), default=1.0)
    scale = max_value if scale_to_max and max_value > 0 else 1.0

    rows = []
    for index, (label, value, caption) in enumerate(items):
        y = top + index * row_height
        actual_width = max(2, int(bar_width * (value / scale)))
        rows.append(
            f'<text x="24" y="{y + 18}" font-size="13" fill="#111827">{escape(label)}</text>'
            f'<rect x="{left}" y="{y}" width="{bar_width}" height="22" rx="4" fill="#e5e7eb"/>'
            f'<rect x="{left}" y="{y}" width="{actual_width}" height="22" rx="4" fill="{color}"/>'
            f'<text x="{width - 24}" y="{y + 16}" text-anchor="end" font-size="12" fill="#374151">{escape(caption)}</text>'
        )

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            f'<text x="24" y="34" font-size="22" font-weight="700" fill="#111827">{escape(title)}</text>',
            f'<text x="24" y="58" font-size="13" fill="#4b5563">{escape(subtitle)}</text>',
            *rows,
            "</svg>",
        ]
    )


def write_latest_results_doc(audit: dict[str, Any], ml_result: dict[str, Any], path: Path) -> None:
    path.write_text(build_results_markdown(audit, ml_result, include_heading=True), encoding="utf-8")


def build_results_markdown(audit: dict[str, Any], ml_result: dict[str, Any], include_heading: bool) -> str:
    lines: list[str] = []
    if include_heading:
        lines.append("# Latest Public Forecast Snapshot")
        lines.append("")
    lines.append(f"Generated UTC: `{audit['generated_at_utc']}`")
    lines.append("")
    lines.append("## Match Forecasts")
    lines.append("")
    lines.append("| Match | Status | Result 90 | P(result) | Score 90 | P(score) |")
    lines.append("|---|---|---|---:|---:|---:|")
    for pred in audit["predictions"]:
        lines.append(
            f"| {pred['match']} | {pred['forecast_status']} | {pred['recommended_result']} | "
            f"{pct(pred['recommended_result_probability'])} | {pred['recommended_score_90']} | "
            f"{pct(pred['recommended_exact_probability_90'])} |"
        )
    lines.append("")
    lines.append("## Tournament Simulation")
    lines.append("")
    lines.append("| Rank | Team | Champion | Final | Semi |")
    lines.append("|---:|---|---:|---:|---:|")
    advancement = audit["tournament"]["advancement"]
    for rank, item in enumerate(audit["tournament"]["champion_top"][:10], start=1):
        values = advancement[item["team"]]
        lines.append(
            f"| {rank} | {item['team']} | {pct(values['champion'])} | "
            f"{pct(values['reach_final'])} | {pct(values['reach_sf'])} |"
        )
    lines.append("")
    lines.append("## Historical ML Backtest")
    lines.append("")
    row_counts = ml_result["row_counts"]
    test = ml_result["test_metrics"]
    elo = ml_result["test_baselines"]["elo_baseline"]
    majority = ml_result["test_baselines"]["majority"]
    lines.append(
        f"Rows: train `{row_counts['train']}`, validation `{row_counts['validation']}`, "
        f"test `{row_counts['test']}`."
    )
    lines.append("")
    lines.append("| Model | Accuracy | Brier | Log loss |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| Softmax ML | {test['accuracy']:.3f} | {test['brier_score']:.3f} | {test['log_loss']:.3f} |")
    lines.append(f"| Elo baseline | {elo['accuracy']:.3f} | {elo['brier_score']:.3f} | {elo['log_loss']:.3f} |")
    lines.append(f"| Majority baseline | {majority['accuracy']:.3f} | {majority['brier_score']:.3f} | {majority['log_loss']:.3f} |")
    lines.append("")
    return "\n".join(lines)


def update_readme_snapshot(audit: dict[str, Any], ml_result: dict[str, Any]) -> None:
    current = README_PATH.read_text(encoding="utf-8")
    start = "<!-- forecast-snapshot:start -->"
    end = "<!-- forecast-snapshot:end -->"
    block = "\n".join(
        [
            start,
            "",
            "## Public Snapshot",
            "",
            "![Exact score probabilities](docs/assets/exact_score_probabilities.svg)",
            "",
            "![Champion probabilities](docs/assets/champion_probabilities.svg)",
            "",
            "![ML backtest log loss](docs/assets/ml_backtest_log_loss.svg)",
            "",
            build_results_markdown(audit, ml_result, include_heading=False).strip(),
            "",
            end,
        ]
    )
    if start in current and end in current:
        before = current.split(start, 1)[0].rstrip()
        after = current.split(end, 1)[1].lstrip()
        next_readme = f"{before}\n\n{block}\n\n{after}"
    else:
        next_readme = f"{current.rstrip()}\n\n{block}\n"
    README_PATH.write_text(next_readme.rstrip() + "\n", encoding="utf-8")


def short_label(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "."


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{100 * value:.1f}%"


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


if __name__ == "__main__":
    sys.exit(main())
