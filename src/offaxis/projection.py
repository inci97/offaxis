"""Projection utilities for simple off-axis transforms."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value into the inclusive ``[minimum, maximum]`` range."""
    return max(minimum, min(maximum, value))


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

    return clamp(nx, -1.0, 1.0), clamp(ny, -1.0, 1.0)


def relative_viewer_offset(
    current_view: tuple[float, float],
    baseline: tuple[float, float],
) -> tuple[float, float]:
    """Compute baseline-relative viewer offset and clamp it into [-1, 1]."""
    vx = clamp(current_view[0] - baseline[0], -1.0, 1.0)
    vy = clamp(current_view[1] - baseline[1], -1.0, 1.0)
    return vx, vy


def smooth_viewer_offset(
    previous_view: tuple[float, float],
    current_view: tuple[float, float],
    alpha: float,
) -> tuple[float, float]:
    """Apply exponential smoothing to viewer offsets.

    ``alpha`` is clamped into ``[0, 1]`` where 0 keeps only the previous value
    and 1 uses only the current value.
    """
    ratio = clamp(alpha, 0.0, 1.0)
    smoothed_x = (previous_view[0] * (1.0 - ratio)) + (current_view[0] * ratio)
    smoothed_y = (previous_view[1] * (1.0 - ratio)) + (current_view[1] * ratio)
    return clamp(smoothed_x, -1.0, 1.0), clamp(smoothed_y, -1.0, 1.0)


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
