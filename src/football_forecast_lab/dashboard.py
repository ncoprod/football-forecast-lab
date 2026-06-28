from __future__ import annotations

import html
import json
from pathlib import Path


def build_dashboard(audit_path: Path, output_path: Path) -> None:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    predictions = audit["predictions"]
    champions = audit["tournament"]["champion_top"][:12]
    advancement = audit["tournament"]["advancement"]

    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(pred['match_paris'])}</td>"
        f"<td>{html.escape(pred['match'])}</td>"
        f"<td>{html.escape(pred['recommended_result'])}</td>"
        f"<td>{pred['recommended_result_probability'] * 100:.1f}%</td>"
        f"<td>{html.escape(pred['recommended_score'])}</td>"
        f"<td>{pred['recommended_exact_probability'] * 100:.1f}%</td>"
        f"<td>{pred['final_outcomes']['home'] * 100:.1f}%</td>"
        f"<td>{pred['final_outcomes']['draw'] * 100:.1f}%</td>"
        f"<td>{pred['final_outcomes']['away'] * 100:.1f}%</td>"
        "</tr>"
        for pred in predictions
    )
    champion_rows = "\n".join(
        "<tr>"
        f"<td>{index}</td>"
        f"<td>{html.escape(item['team'])}</td>"
        f"<td>{advancement[item['team']]['champion'] * 100:.1f}%</td>"
        f"<td>{advancement[item['team']]['reach_final'] * 100:.1f}%</td>"
        f"<td>{advancement[item['team']]['reach_sf'] * 100:.1f}%</td>"
        "</tr>"
        for index, item in enumerate(champions, start=1)
    )
    output_path.write_text(render_html(rows, champion_rows), encoding="utf-8")


def render_html(match_rows: str, champion_rows: str) -> str:
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Football Forecast Lab</title>
  <style>
    :root {{ color-scheme: light; font-family: Arial, sans-serif; }}
    body {{ margin: 0; background: #f5f7fb; color: #111827; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 28px; margin: 0 0 18px; }}
    h2 {{ font-size: 18px; margin: 28px 0 10px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d8dde5; box-shadow: 0 1px 2px rgba(17, 24, 39, 0.05); }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e6e9ee; text-align: left; font-size: 14px; }}
    th {{ background: #eef2f7; font-weight: 700; }}
    td:nth-child(n+4) {{ font-variant-numeric: tabular-nums; }}
    @media (max-width: 760px) {{
      main {{ padding: 14px; }}
      table {{ display: block; overflow-x: auto; white-space: nowrap; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>Football Forecast Lab</h1>
  <h2>Pronostics scores</h2>
  <table>
    <thead><tr><th>Date</th><th>Match</th><th>Resultat</th><th>P(resultat)</th><th>Score</th><th>P(score)</th><th>Home</th><th>Nul</th><th>Away</th></tr></thead>
    <tbody>{match_rows}</tbody>
  </table>
  <h2>Simulation champion</h2>
  <table>
    <thead><tr><th>Rang</th><th>Equipe</th><th>Champion</th><th>Finale</th><th>Demi</th></tr></thead>
    <tbody>{champion_rows}</tbody>
  </table>
</main>
</body>
</html>
"""
