"""Projection utilities for simple off-axis transforms."""

from __future__ import annotations


def normalize_viewer_offset(
    face_x: float,
    face_y: float,
    frame_width: float,
    frame_height: float,
) -> tuple[float, float]:
    """Normalize face location into [-1, 1] range around frame center."""
    if frame_width <= 0 or frame_height <= 0:
        return 0.0, 0.0

    nx = ((face_x / frame_width) - 0.5) * 2.0
    ny = ((face_y / frame_height) - 0.5) * 2.0

    nx = max(-1.0, min(1.0, nx))
    ny = max(-1.0, min(1.0, ny))
    return nx, ny


def quad_from_view(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    view_x: float,
    view_y: float,
    strength: float = 0.25,
) -> list[tuple[float, float]]:
    """Create a perspective-skewed quad representing off-axis projection.

    The near edge appears larger based on viewer offset.
    """
    half_w = width / 2.0
    half_h = height / 2.0

    sx = view_x * strength * width
    sy = view_y * strength * height

    tl = (center_x - half_w - sx, center_y - half_h - sy)
    tr = (center_x + half_w - sx, center_y - half_h + sy)
    br = (center_x + half_w + sx, center_y + half_h + sy)
    bl = (center_x - half_w + sx, center_y + half_h - sy)

    return [tl, tr, br, bl]
