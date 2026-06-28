# ML Training Report

Source: `martj42/international_results results.csv`

## Rows

| Split | Rows |
|---|---:|
| train | 18164 |
| validation | 3581 |
| test | 3670 |
| total | 25415 |

## Best Validation Model

```json
{
  "model": "softmax",
  "feature_set": "elo",
  "learning_rate": 0.02,
  "l2": 0.0005,
  "epochs": 24,
  "validation": {
    "accuracy": 0.6084892488131807,
    "brier_score": 0.5063214210959108,
    "log_loss": 0.8632369163719403
  }
}
```

## Test Metrics

```json
{
  "accuracy": 0.6059945504087193,
  "brier_score": 0.5103299592341389,
  "log_loss": 0.86832558650028
}
```

## Test Baselines

```json
{
  "majority": {
    "accuracy": 0.47220708446866483,
    "brier_score": 0.6358473159606062,
    "log_loss": 1.053722060785767
  },
  "elo_baseline": {
    "accuracy": 0.6051771117166213,
    "brier_score": 0.5421506168720944,
    "log_loss": 0.9262634230051808
  }
}
```

## Validation Leaderboard

| Rank | Model | Features | Log loss | Brier | Accuracy |
|---:|---|---|---:|---:|---:|
| 1 | softmax | elo | 0.8632 | 0.5063 | 0.6085 |
| 2 | softmax | elo | 0.8633 | 0.5064 | 0.6096 |
| 3 | softmax | elo_form | 0.8699 | 0.5098 | 0.6021 |
| 4 | softmax | elo_form | 0.8701 | 0.5100 | 0.6015 |
| 5 | softmax | full | 0.8708 | 0.5103 | 0.6046 |
| 6 | softmax | full | 0.8709 | 0.5104 | 0.6060 |
| 7 | softmax | elo | 0.8725 | 0.5125 | 0.5979 |
| 8 | softmax | elo | 0.8729 | 0.5126 | 0.5970 |
| 9 | softmax | elo | 0.8808 | 0.5192 | 0.5973 |
| 10 | softmax | elo | 0.8818 | 0.5199 | 0.5962 |
| 11 | softmax | elo_form | 0.8985 | 0.5313 | 0.5716 |
| 12 | softmax | elo_form | 0.8993 | 0.5320 | 0.5711 |
| 13 | softmax | elo | 0.9045 | 0.5357 | 0.5552 |
| 14 | softmax | elo | 0.9066 | 0.5371 | 0.5518 |
| 15 | softmax | elo_form | 0.9074 | 0.5287 | 0.5909 |

## Interpretation

This is a first trained model using historical international results and pre-match chronological features. It does not include historical bookmaker odds yet, so it should be treated as an ML layer to compare against market-calibrated live models, not as a replacement for market odds.
