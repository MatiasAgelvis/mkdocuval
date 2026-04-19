#!/usr/bin/env python3
# coding: utf-8

import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from card_models import Card


@dataclass
class SourceBuildResult:
    source_path: Path
    cards: list[Card]


@dataclass
class CardLengthAnomaly:
    source_path: str
    card_id: str
    page: Optional[str]
    char_count: int
    mean_chars: float
    stdev_chars: float
    source_share: float
    reasons: list[str]
    raw_marker: Optional[str] = None
    zscore: Optional[float] = None


def collect_card_length_anomalies(
    source_results: list[SourceBuildResult],
    sigma_threshold: float,
    min_chars: int,
    max_chars: int,
    source_share_threshold: float,
    relative_ratio_threshold: float,
) -> list[CardLengthAnomaly]:
    anomalies: list[CardLengthAnomaly] = []

    for result in source_results:
        char_counts = [len(card.content.strip()) for card in result.cards]
        if not char_counts:
            continue

        mean_chars = statistics.fmean(char_counts)
        stdev_chars = statistics.pstdev(char_counts) if len(char_counts) > 1 else 0.0
        total_chars = sum(char_counts)

        for card, char_count in zip(result.cards, char_counts):
            reasons: list[str] = []
            zscore: Optional[float] = None
            source_share = (char_count / total_chars) if total_chars else 0.0
            relative_to_mean = (char_count / mean_chars) if mean_chars else 0.0

            if char_count == 0:
                reasons.append("empty")
            elif char_count <= min_chars:
                reasons.append(f"tiny (<={min_chars} chars)")

            if char_count >= max_chars:
                reasons.append(f"huge (>={max_chars} chars)")

            if stdev_chars > 0:
                zscore = (char_count - mean_chars) / stdev_chars
                if zscore >= sigma_threshold and relative_to_mean >= relative_ratio_threshold:
                    reasons.append(f"long z={zscore:.2f}")
                elif zscore <= -sigma_threshold and relative_to_mean <= (1 / relative_ratio_threshold):
                    reasons.append(f"short z={zscore:.2f}")

            if len(result.cards) > 1 and source_share >= source_share_threshold:
                reasons.append(f"dominates source ({source_share:.1%})")

            if reasons:
                anomalies.append(
                    CardLengthAnomaly(
                        source_path=result.source_path.as_posix(),
                        card_id=card.id,
                        page=card.page,
                        char_count=char_count,
                        mean_chars=mean_chars,
                        stdev_chars=stdev_chars,
                        source_share=source_share,
                        reasons=reasons,
                        raw_marker=card.raw_marker,
                        zscore=zscore,
                    )
                )

    def anomaly_sort_key(anomaly: CardLengthAnomaly) -> tuple[int, float, int, float]:
        reason_weight = 0
        if any(reason.startswith("huge") or reason.startswith("long") for reason in anomaly.reasons):
            reason_weight = 3
        elif any(reason.startswith("empty") or reason.startswith("tiny") or reason.startswith("short") for reason in anomaly.reasons):
            reason_weight = 2
        elif any(reason.startswith("dominates source") for reason in anomaly.reasons):
            reason_weight = 1

        return (
            reason_weight,
            abs(anomaly.zscore) if anomaly.zscore is not None else 0.0,
            anomaly.char_count,
            anomaly.source_share,
        )

    return sorted(anomalies, key=anomaly_sort_key, reverse=True)


def print_card_length_anomalies(anomalies: list[CardLengthAnomaly]) -> None:
    if not anomalies:
        return

    print("Possible card-length anomalies:")
    for anomaly in anomalies:
        page = anomaly.page or "?"
        zscore = f"{anomaly.zscore:+.2f}" if anomaly.zscore is not None else "n/a"
        print(
            "- "
            f"{anomaly.source_path} "
            f"card={anomaly.card_id} "
            f"page={page} "
            f"chars={anomaly.char_count} "
            f"mean={anomaly.mean_chars:.1f} "
            f"stdev={anomaly.stdev_chars:.1f} "
            f"z={zscore} "
            f"share={anomaly.source_share:.1%} "
            f"reasons={'; '.join(anomaly.reasons)}"
        )
        if anomaly.raw_marker:
            marker_preview = re.sub(r"\s+", " ", anomaly.raw_marker).strip()
            if len(marker_preview) > 120:
                marker_preview = marker_preview[:117] + "..."
            print(f"  marker={marker_preview}")
