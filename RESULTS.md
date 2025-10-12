# Benchmark Results

This document presents the performance of the `dual_substrate` model against the baselines on the recall and drift task. The key metrics are:

-   **`recall@1`**: The fraction of learned facts that were correctly recalled. Higher is better.
-   **`drift_rate`**: The fraction of control probes that were incorrectly stored in memory. Lower is better.
-   **`retention_half_life`**: The number of turns after which the model fails to recall a fact. Higher is better.
-   **`tokens_per_s`**: The processing speed of the model. Higher is better.

## Performance Comparison

| Model                | Recall@1 | Drift Rate | Retention Half-Life | Tokens/s |
| -------------------- | -------- | ---------- | ------------------- | -------- |
| `dual_substrate`     | 0.95     | 0.0        | 300                 | ~285     |
| `lstm_baseline`      | 0.90     | 0.0        | 300                 | ~7351    |

## Analysis

-   The `dual_substrate` model achieves a slightly higher **recall rate** (95%) compared to the `lstm_baseline` (90%), indicating a small advantage in memory accuracy.
-   Both models exhibit a perfect **drift rate** of 0.0, meaning they did not incorrectly store any unlearned symbols.
-   The **retention half-life** is identical for both models in this test configuration.
-   The `lstm_baseline` is significantly **faster** (`~7351 tokens/s`) than the `dual_substrate` model (`~285 tokens/s`). This is expected, as the `dual_substrate` model's projector operations are computationally intensive.

These results suggest that the `dual_substrate` model offers a modest improvement in recall accuracy at the cost of significantly higher computational overhead. Further work could explore optimizing the performance of the continuous cache or investigating whether the recall advantage holds up in more complex tasks.