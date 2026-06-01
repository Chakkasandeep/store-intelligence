"""Normalized zone ROIs per camera role — derived from layout, not hardcoded store IDs."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ZoneROI:
    zone_id: str
    polygon: list[tuple[float, float]]  # normalized x,y


def rois_for_role(role: str) -> list[ZoneROI]:
    """Return zone polygons in normalized image coordinates for a camera role."""
    if role == "entry":
        return [
            ZoneROI("ENTRY_EXIT", [(0.35, 0.35), (0.95, 0.35), (0.95, 0.95), (0.35, 0.95)]),
            ZoneROI("FOH_CENTER", [(0.0, 0.4), (0.5, 0.4), (0.5, 1.0), (0.0, 1.0)]),
        ]
    if role == "billing":
        return [
            ZoneROI("BILLING", [(0.0, 0.2), (0.75, 0.2), (0.75, 0.95), (0.0, 0.95)]),
            ZoneROI("ACCESSORIES", [(0.7, 0.0), (1.0, 0.0), (1.0, 1.0), (0.7, 1.0)]),
        ]
    return [
        ZoneROI("FOH_CENTER", [(0.2, 0.3), (0.8, 0.3), (0.8, 0.95), (0.2, 0.95)]),
        ZoneROI("SKIN_NORTH", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.35), (0.0, 0.35)]),
        ZoneROI("MAKEUP_SOUTH", [(0.0, 0.65), (1.0, 0.65), (1.0, 1.0), (0.0, 1.0)]),
    ]


def point_in_polygon(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1):
            inside = not inside
    return inside


def zone_for_point(x_norm: float, y_norm: float, role: str) -> str | None:
    for roi in rois_for_role(role):
        if point_in_polygon(x_norm, y_norm, roi.polygon):
            return roi.zone_id
    return None
