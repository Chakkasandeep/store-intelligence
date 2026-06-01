"""Heuristic staff detection from track persistence and movement."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrackStats:
    frames: int = 0
    total_movement: float = 0.0
    zones: set[str] = field(default_factory=set)
    camera_roles: set[str] = field(default_factory=set)


def classify_staff(stats: TrackStats, clip_frames: int) -> tuple[bool, float]:
    persistence = stats.frames / max(clip_frames, 1)
    movement = stats.total_movement / max(stats.frames, 1)
    score = 0.0
    if persistence > 0.35:
        score += 0.35
    if movement > 8.0:
        score += 0.25
    if "billing" in stats.camera_roles and persistence > 0.2:
        score += 0.25
    if len(stats.zones) >= 3:
        score += 0.15
    return score >= 0.55, min(0.99, score)
