"""Lightweight appearance Re-ID for visitor tokens (CPU-friendly)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Appearance:
    hist: np.ndarray
    visitor_id: str
    last_seen: float = 0.0
    total_frames: int = 0


class ReIDBank:
    def __init__(self, threshold: float = 0.55) -> None:
        self.threshold = threshold
        self._bank: list[Appearance] = []

    @staticmethod
    def _hist(crop: np.ndarray) -> np.ndarray:
        if crop.size == 0:
            return np.zeros(256, dtype=np.float32)
        if crop.ndim == 2:
            crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        return hist.flatten().astype(np.float32)

    def match_or_create(self, crop: np.ndarray, ts: float) -> tuple[str, float]:
        hist = self._hist(crop)
        best_id = None
        best_dist = 1.0
        for app in self._bank:
            dist = float(
                cv2.compareHist(
                    app.hist.reshape(-1, 1), hist.reshape(-1, 1), cv2.HISTCMP_BHATTACHARYYA
                )
            )
            if dist < best_dist:
                best_dist = dist
                best_id = app.visitor_id
        if best_id is not None and best_dist < self.threshold:
            for app in self._bank:
                if app.visitor_id == best_id:
                    app.last_seen = ts
                    app.total_frames += 1
            return best_id, 1.0 - best_dist
        vid = f"VIS_{uuid.uuid4().hex[:8]}"
        self._bank.append(Appearance(hist=hist, visitor_id=vid, last_seen=ts, total_frames=1))
        return vid, 0.7
