from __future__ import annotations

import csv
import json
from datetime import datetime
from typing import Any

from .settings import (
    ELO_BASE,
    GROUP_SCOREBOARD_URL,
    KNOCKOUT_SCOREBOARD_URL,
    NEWS_URL,
    OUTPUT_DIR,
    PARIS_TZ,
    R32_SCOREBOARD_URL,
)
from .utils import fmt_float, pct, serialize_datetimes
from .features import write_feature_store

def format_group(stats: dict[str, Any]) -> str:
    if not stats:
        return "n/a"
    return (
        f"{stats.get('points', 0)} pts, "
        f"{stats.get('gf', 0)}-{stats.get('ga', 0)} buts, "
        f"forme {stats.get('form_string', '')}"
    )

def format_elo(elo: dict[str, Any]) -> str:
    if not elo.get("available"):
        return "n/a"
    rank = f"#{elo.get('rank')}" if elo.get("rank") else "rang n/a"
    return f"{elo.get('rating')} ({rank}, {elo.get('date')})"

def format_leaders(leaders: dict[str, Any]) -> str:
    goals = leaders.get("top_goals", [])
    assists = leaders.get("top_assists", [])
    parts = []
    if goals:
        parts.append("buteurs: " + ", ".join(f"{item['name']} {fmt_float(item['value'], 0)}" for item in goals[:2]))
    if assists:
        parts.append("passes: " + ", ".join(f"{item['name']} {fmt_float(item['value'], 0)}" for item in assists[:1]))
    return "; ".join(parts) if parts else "n/a"

def write_outputs(
    predictions: list[dict[str, Any]],
    group_stats: dict[str, dict[str, Any]],
    elo_map: dict[str, dict[str, Any]],
    tournament: dict[str, Any],
    optional_odds: dict[str, Any],
    generated_at: datetime,
    config: dict[str, Any],
) -> None:
    csv_path = OUTPUT_DIR / "mpp_pronostics_2026_16es.csv"
    champion_csv_path = OUTPUT_DIR / "mpp_champion_simulation_2026.csv"
    feature_store_path = OUTPUT_DIR / "feature_store_current_matches.csv"
    json_path = OUTPUT_DIR / "mpp_pronostics_2026_16es_audit.json"
    report_path = OUTPUT_DIR / "mpp_pronostics_2026_16es.md"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "match_paris",
                "match",
                "prono_recommande",
                "confiance",
                "risque",
                "p_score_exact",
                "p_home_apres_prolong",
                "p_draw_apres_prolong",
                "p_away_apres_prolong",
                "score_prudent",
                "score_agressif",
                "cotes_marche",
                "lambda_home_90",
                "lambda_away_90",
                "elo_home",
                "elo_away",
                "forme_home",
                "forme_away",
                "source",
            ],
        )
        writer.writeheader()
        for pred in predictions:
            writer.writerow(
                {
                    "match_paris": pred["match_paris"],
                    "match": pred["match"],
                    "prono_recommande": pred["recommended_score"],
                    "confiance": pred["confidence"],
                    "risque": pred["risk"],
                    "p_score_exact": pct(pred["recommended_exact_probability"]),
                    "p_home_apres_prolong": pct(pred["final_outcomes"]["home"]),
                    "p_draw_apres_prolong": pct(pred["final_outcomes"]["draw"]),
                    "p_away_apres_prolong": pct(pred["final_outcomes"]["away"]),
                    "score_prudent": pred["safe_score"],
                    "score_agressif": pred["aggressive_score"],
                    "cotes_marche": pred["odds"].get("details", ""),
                    "lambda_home_90": fmt_float(pred["lambda_home_90"]),
                    "lambda_away_90": fmt_float(pred["lambda_away_90"]),
                    "elo_home": format_elo(pred["elo_home"]),
                    "elo_away": format_elo(pred["elo_away"]),
                    "forme_home": format_group(pred["group_home"]),
                    "forme_away": format_group(pred["group_away"]),
                    "source": pred["source_url"],
                }
            )

    write_feature_store(feature_store_path, predictions)

    with champion_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "team",
                "rating_model",
                "elo_base",
                "reach_r16",
                "reach_qf",
                "reach_sf",
                "reach_final",
                "champion",
                "market_nudge",
                "group_nudge",
            ],
        )
        writer.writeheader()
        for team, values in sorted(
            tournament["advancement"].items(),
            key=lambda item: item[1]["champion"],
            reverse=True,
        ):
            writer.writerow(
                {
                    "team": team,
                    "rating_model": fmt_float(values["rating"], 1),
                    "elo_base": fmt_float(values["base_elo"], 0),
                    "reach_r16": pct(values["reach_r16"]),
                    "reach_qf": pct(values["reach_qf"]),
                    "reach_sf": pct(values["reach_sf"]),
                    "reach_final": pct(values["reach_final"]),
                    "champion": pct(values["champion"]),
                    "market_nudge": fmt_float(values["market_nudge"], 1),
                    "group_nudge": fmt_float(values["group_nudge"], 1),
                }
            )

    audit_payload = {
        "generated_at_utc": generated_at.isoformat(),
        "config": config,
        "sources": {
            "espn_group_scoreboard": GROUP_SCOREBOARD_URL,
            "espn_round_of_32_scoreboard": R32_SCOREBOARD_URL,
            "espn_future_knockout_scoreboard": KNOCKOUT_SCOREBOARD_URL,
            "espn_news": NEWS_URL,
            "elo_base": ELO_BASE,
        },
        "predictions": predictions,
        "tournament": tournament,
        "optional_odds": optional_odds,
        "group_stats": serialize_datetimes(group_stats),
        "elo_map": elo_map,
    }
    json_path.write_text(json.dumps(serialize_datetimes(audit_payload), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(predictions, tournament, optional_odds, generated_at, config), encoding="utf-8")

def build_report(
    predictions: list[dict[str, Any]],
    tournament: dict[str, Any],
    optional_odds: dict[str, Any],
    generated_at: datetime,
    config: dict[str, Any],
) -> str:
    lines: list[str] = []
    lines.append("# Pronostics MPP - Coupe du monde 2026, 16es de finale")
    lines.append("")
    lines.append(f"Genere le {generated_at.astimezone(PARIS_TZ).strftime('%Y-%m-%d %H:%M')} Europe/Paris.")
    lines.append("")
    lines.append("## Synthese rapide")
    lines.append("")
    lines.append("| Date Paris | Match | Prono | Confiance | Score exact | Prudent | Agressif |")
    lines.append("|---|---|---:|---|---:|---:|---:|")
    for pred in predictions:
        lines.append(
            "| "
            + " | ".join(
                [
                    pred["match_paris"],
                    pred["match"],
                    pred["recommended_score"],
                    pred["confidence"],
                    pct(pred["recommended_exact_probability"]),
                    pred["safe_score"],
                    pred["aggressive_score"],
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Simulation champion")
    lines.append("")
    lines.append("| Rang | Equipe | Champion | Finale | Demi | Quart |")
    lines.append("|---:|---|---:|---:|---:|---:|")
    for rank, item in enumerate(tournament["champion_top"][:12], start=1):
        values = tournament["advancement"][item["team"]]
        lines.append(
            f"| {rank} | {item['team']} | {pct(values['champion'])} | "
            f"{pct(values['reach_final'])} | {pct(values['reach_sf'])} | {pct(values['reach_qf'])} |"
        )

    lines.append("")
    lines.append("## Methode")
    lines.append("")
    lines.append("- Source principale: endpoints JSON ESPN FIFA World Cup 2026 pour calendrier, resultats, cotes, leaders, rosters et actus.")
    lines.append("- Source force equipe: fichiers TSV publics World Football Elo.")
    lines.append("- Cotes externes optionnelles: The Odds API est branche via `THE_ODDS_API_KEY`; API-Football est documente via `API_FOOTBALL_KEY` mais non appele tant que le matching fixture live n'est pas verifie.")
    lines.append("- Modele: ajustement Poisson sur cotes 1N2 + total buts, puis nudges controles avec Elo, forme de groupe, repos et leaders joueurs.")
    lines.append("- Knockout/MPP: le score recommande est simule apres prolongation quand le match est nul a 90 minutes; les tirs au but ne changent pas le score.")
    lines.append("- Simulation champion: propagation exacte des probabilites dans le bracket ESPN; en cas de nul apres prolongation, les tirs au but sont alloues par force relative modele.")
    lines.append("- Les coefficients MPP exacts ne sont pas publics dans ces sources; le scoring est configurable dans `work/mpp_worldcup_2026/mpp_config.json`.")
    lines.append("")
    lines.append("Config active: `" + json.dumps(config, ensure_ascii=False) + "`")
    lines.append("")
    lines.append("Statut sources odds: `" + json.dumps(optional_odds.get("sources", {}), ensure_ascii=False) + "`")
    lines.append("")
    lines.append("## Details par match")
    lines.append("")

    for pred in predictions:
        home_name = pred["home"]["name"]
        away_name = pred["away"]["name"]
        lines.append(f"### {pred['match_paris']} - {home_name} vs {away_name}")
        lines.append("")
        lines.append(f"Prono recommande: **{pred['recommended_score']}** ({pred['confidence']}, risque {pred['risk']}).")
        lines.append(
            "Probabilites apres prolongation: "
            f"{home_name} {pct(pred['final_outcomes']['home'])}, "
            f"nul {pct(pred['final_outcomes']['draw'])}, "
            f"{away_name} {pct(pred['final_outcomes']['away'])}."
        )
        lines.append(
            "Scores les plus probables: "
            + ", ".join(f"{item['score']} ({pct(item['probability'])})" for item in pred["top_scores"][:5])
            + "."
        )
        lines.append(f"Cotes marche ESPN/DraftKings: `{pred['odds'].get('details', 'n/a')}`.")
        lines.append(f"Forme groupe {home_name}: {format_group(pred['group_home'])}.")
        lines.append(f"Forme groupe {away_name}: {format_group(pred['group_away'])}.")
        lines.append(f"Elo {home_name}: {format_elo(pred['elo_home'])}; Elo {away_name}: {format_elo(pred['elo_away'])}.")
        lines.append(f"Leaders {home_name}: {format_leaders(pred['leaders_home'])}.")
        lines.append(f"Leaders {away_name}: {format_leaders(pred['leaders_away'])}.")
        if pred["news_notes"]:
            clean_news = []
            for note in pred["news_notes"][:3]:
                risk = f" [risque: {note['risk_terms']}]" if note.get("risk_terms") else ""
                clean_news.append(f"{note['headline']}{risk}")
            lines.append("Actu prise en compte: " + " / ".join(clean_news) + ".")
        lines.append(f"Source match: {pred['source_url']}")
        lines.append("")

    lines.append("## Limites importantes")
    lines.append("")
    lines.append("- Les cotes ESPN/DraftKings sont traitees comme une baseline marche; elles peuvent etre differentes des cotes MPP visibles dans ton app.")
    lines.append("- Les actus sont integrees par headlines/categories ESPN, pas par scraping medical profond. Une annonce de composition a 1h du match doit etre verifiee manuellement.")
    lines.append("- Deep learning non force: sans historique riche et comparable avec labels MPP, un reseau neuronal donnerait une fausse precision. Le modele probabiliste + marche est plus robuste ici.")
    return "\n".join(lines) + "\n"

