"""ML dispatch stub for DoubleDQN training.

Replace the ``train`` function body with a real stable-baselines3 DoubleDQN
training loop.  The stub simulates training metrics so the rest of the
pipeline (threading, persistence, status updates) can be exercised without
a GPU or heavy dependencies.

Production replacement notes:
  - Instantiate a stable-baselines3 DQN (or custom DoubleDQN) with
    ``policy="MlpPolicy"``, ``learning_rate=config.learning_rate``,
    ``buffer_size=config.buffer_size``, and ``net_arch`` parsed from
    ``config.net_arch``.
  - Call ``model.learn(total_timesteps=config.timesteps, callback=...)``.
  - Save with ``model.save(config.output_dir + "/" + filename)``.
  - Collect per-episode metrics from a custom callback and return them in
    ``TrainingOutcome.episode_metrics``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Configuration & result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TrainingConfig:
    run_id: str
    model_version: str
    algorithm: str
    timesteps: int
    learning_rate: float
    buffer_size: int
    net_arch: str
    exploration_pct: float
    output_dir: str


@dataclass
class TrainingOutcome:
    model_path: str
    sharpe: float
    max_drawdown: float
    total_return: float
    episode_metrics: list[dict] = field(default_factory=list)
    """Each dict contains: episode, reward, loss, epsilon, portfolio_value."""


# ---------------------------------------------------------------------------
# Stub implementation
# ---------------------------------------------------------------------------


def train(config: TrainingConfig) -> TrainingOutcome:
    """Run DoubleDQN training and return outcome metrics.

    **Stub** — replace this body with a real stable-baselines3 training loop.
    See module-level docstring for migration notes.

    The stub:
    - Sleeps for ``min(timesteps / 1_000_000, 0.05)`` seconds.
    - Generates ``min(max(1, timesteps // 1000), 200)`` episode entries where
      reward improves linearly from -50 to +50, epsilon decays from
      ``exploration_pct`` to 0.05, portfolio_value grows from 1.0 to 1.3,
      and loss decays from 1.0 to 0.01.
    - Returns fixed sharpe=1.42, max_drawdown=-0.12, total_return=0.28.
    """
    sleep_secs = min(config.timesteps / 1_000_000, 0.05)
    time.sleep(sleep_secs)

    n_episodes = min(max(1, config.timesteps // 1000), 200)

    episode_metrics: list[dict] = []
    for i in range(n_episodes):
        t = i / max(n_episodes - 1, 1)  # 0.0 → 1.0
        episode_metrics.append(
            {
                "episode": i + 1,
                "reward": -50.0 + 100.0 * t,
                "loss": 1.0 - 0.99 * t,
                "epsilon": config.exploration_pct - (config.exploration_pct - 0.05) * t,
                "portfolio_value": 1.0 + 0.3 * t,
            }
        )

    model_filename = f"{config.model_version}_{config.run_id[:8]}.zip"
    model_path = f"{config.output_dir}/{model_filename}"

    return TrainingOutcome(
        model_path=model_path,
        sharpe=1.42,
        max_drawdown=-0.12,
        total_return=0.28,
        episode_metrics=episode_metrics,
    )
