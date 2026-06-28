# Model Card

## Current model

The live decision model is market-calibrated and probabilistic. A first trained ML layer is also included as an advisory signal.

It combines:

- ESPN/DraftKings market odds,
- optional The Odds API multi-book odds,
- World Football Elo,
- group-stage form,
- rest days,
- ESPN tournament player leaders,
- Poisson score distributions,
- extra-time and bracket simulation.
- historical softmax regression trained on international results since 2000.

## Why this is the right baseline

Football betting markets encode a large amount of current information. A simple model calibrated to market odds plus controlled football features is a stronger starting point than an unvalidated neural network.

## What would make ML worthwhile

The first ML pass is implemented with chronological pre-match features. It improves log loss/Brier over simple baselines, but it still lacks historical odds and player availability.

Further ML becomes more useful after adding:

- historical odds,
- Elo/FIFA ranking before match,
- team form before match,
- player availability before match,
- score/result labels,
- tournament stage and context.

The next trained model should likely be LightGBM or CatBoost, then calibrated. Deep learning should come later, only with enough player/event/xG history.

## Current limitations

- Multi-book odds require optional personal API keys stored only in local `.env`.
- No bundled historical odds archive yet.
- Player form is limited to ESPN tournament leaders.
- Exact scorer/player prop forecasts are not active yet; they need lineups, expected minutes, injuries and player prop odds before they are worth publishing.
- This repo is a decision-support lab, not an automatic real-money betting bot.
