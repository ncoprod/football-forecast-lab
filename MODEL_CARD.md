# Model Card

## Current model

This is a market-calibrated probabilistic model, not a trained deep-learning model.

It combines:

- ESPN/DraftKings market odds,
- World Football Elo,
- group-stage form,
- rest days,
- ESPN tournament player leaders,
- Poisson score distributions,
- extra-time and bracket simulation.

## Why this is the right baseline

Football betting markets encode a large amount of current information. A simple model calibrated to market odds plus controlled football features is a stronger starting point than an unvalidated neural network.

## What would make ML worthwhile

Trainable ML becomes useful after building a historical dataset with pre-match-only features:

- historical odds,
- Elo/FIFA ranking before match,
- team form before match,
- player availability before match,
- score/result labels,
- tournament stage and context.

The first trained model should likely be LightGBM or CatBoost, then calibrated. Deep learning should come later, only with enough player/event/xG history.

## Current limitations

- Multi-book odds require optional personal API keys.
- No bundled historical odds archive yet.
- Player form is limited to ESPN tournament leaders.
- MPP proprietary scoring coefficients are configurable, not scraped.
