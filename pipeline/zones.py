"""Check point-in-polygon containment dynamically using coordinates from store layout config."""
from __future__ import annotations


def point_in_polygon(x: float, y: float, poly: list[list[float]]) -> bool:
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1):
            inside = not inside
    return inside


def zone_for_point(x_norm: float, y_norm: float, role: str, layout: dict) -> str | None:
    """Return matching zone_id for point using polygons specified in layout dict."""
    role_polygons = layout.get("role_polygons", {})
    rois = role_polygons.get(role, [])
    for roi in rois:
        zone_id = roi.get("zone_id")
        polygon = roi.get("polygon")
        if zone_id and polygon:
            if point_in_polygon(x_norm, y_norm, polygon):
                return zone_id
    return None
