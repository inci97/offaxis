"""Camera-based OffAxis prototype app."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from .projection import (
    normalize_viewer_offset,
    quad_from_view,
    relative_viewer_offset,
    smooth_viewer_offset,
)


CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


@dataclass(frozen=True)
class PanelSpec:
    """Panel content + transform parameters."""

    title: str
    size: tuple[int, int]
    color: tuple[int, int, int]
    center: tuple[float, float]
    scale: float
    strength: float


PANEL_LAYOUTS: dict[str, list[PanelSpec]] = {
    "default": [
        PanelSpec("Screen A", (460, 300), (60, 190, 255), (0.35, 0.52), 1.0, 0.18),
        PanelSpec("Screen B", (420, 260), (140, 100, 255), (0.68, 0.44), 0.75, 0.22),
        PanelSpec("Screen C", (360, 220), (60, 220, 160), (0.62, 0.72), 0.55, 0.15),
    ],
    "focus": [
        PanelSpec("Screen A", (540, 340), (60, 190, 255), (0.50, 0.52), 1.0, 0.22),
        PanelSpec("Screen B", (330, 210), (140, 100, 255), (0.23, 0.42), 0.60, 0.17),
        PanelSpec("Screen C", (330, 210), (60, 220, 160), (0.77, 0.66), 0.60, 0.17),
    ],
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OffAxis camera projection prototype")
    parser.add_argument(
        "--layout",
        choices=sorted(PANEL_LAYOUTS.keys()),
        default="default",
        help="Panel layout preset.",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        default=0.30,
        help="Offset smoothing ratio in [0,1]. Higher = more responsive.",
    )
    parser.add_argument(
        "--debug-face",
        action="store_true",
        help="Draw detected face bounding box in camera view.",
    )
    return parser.parse_args()


def _draw_panel_content(title: str, size: tuple[int, int], color: tuple[int, int, int]) -> np.ndarray:
    w, h = size
    panel = np.zeros((h, w, 3), dtype=np.uint8)
    panel[:, :] = tuple(int(c * 0.22) for c in color)

    cv2.rectangle(panel, (0, 0), (w - 1, h - 1), color, 2)
    cv2.rectangle(panel, (0, 0), (w - 1, 26), tuple(min(255, c + 30) for c in color), -1)
    cv2.putText(panel, title, (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (245, 245, 245), 1, cv2.LINE_AA)

    for i in range(6):
        y = 40 + i * 24
        cv2.rectangle(panel, (12, y), (w - 12, y + 16), (40, 40, 40), -1)
        cv2.rectangle(panel, (12, y), (int(w * 0.35), y + 16), tuple(int(c * 0.9) for c in color), -1)

    return panel


def _warp_panel(canvas: np.ndarray, panel: np.ndarray, quad: list[tuple[float, float]]) -> None:
    h, w = panel.shape[:2]
    src = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    dst = np.array(quad, dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(panel, matrix, (canvas.shape[1], canvas.shape[0]))

    mask = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
    inv_mask = cv2.bitwise_not(mask)

    bg = cv2.bitwise_and(canvas, canvas, mask=inv_mask)
    fg = cv2.bitwise_and(warped, warped, mask=mask)
    canvas[:] = cv2.add(bg, fg)


def _scale_color(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)


def _draw_box_frame(
    canvas: np.ndarray,
    quad: list[tuple[float, float]],
    color: tuple[int, int, int],
    view: tuple[float, float],
    strength: float,
) -> None:
    front = np.array(quad, dtype=np.float32)

    eye = np.array(
        [
            (canvas.shape[1] * 0.5) + (view[0] * canvas.shape[1] * 0.52),
            (canvas.shape[0] * 0.5) + (view[1] * canvas.shape[0] * 0.52),
        ],
        dtype=np.float32,
    )

    depth = 0.34 + (strength * 0.9)
    back = eye + (front - eye) * depth

    front_lines = np.round(front).astype(np.int32)
    back_lines = np.round(back).astype(np.int32)

    overlay = canvas.copy()
    cv2.fillConvexPoly(overlay, back_lines, _scale_color(color, 0.22), lineType=cv2.LINE_AA)

    side_shades = (0.20, 0.24, 0.30, 0.26)
    for i in range(4):
        j = (i + 1) % 4
        side = np.array([front_lines[i], front_lines[j], back_lines[j], back_lines[i]], dtype=np.int32)
        cv2.fillConvexPoly(overlay, side, _scale_color(color, side_shades[i]), lineType=cv2.LINE_AA)

    cv2.addWeighted(overlay, 0.60, canvas, 0.40, 0.0, dst=canvas)

    cv2.polylines(canvas, [back_lines], isClosed=True, color=_scale_color(color, 0.90), thickness=2, lineType=cv2.LINE_AA)
    for i in range(4):
        cv2.line(
            canvas,
            tuple(front_lines[i]),
            tuple(back_lines[i]),
            _scale_color(color, 0.80),
            2,
            cv2.LINE_AA,
        )
    cv2.polylines(canvas, [front_lines], isClosed=True, color=_scale_color(color, 1.25), thickness=3, lineType=cv2.LINE_AA)


def _detect_face(gray: np.ndarray, face_detector: cv2.CascadeClassifier) -> Optional[tuple[float, float, tuple[int, int, int, int]]]:
    faces = face_detector.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return x + w / 2.0, y + h / 2.0, (int(x), int(y), int(w), int(h))


def main() -> None:
    args = _parse_args()
    smoothing = max(0.0, min(1.0, args.smoothing))
    layout = PANEL_LAYOUTS[args.layout]

    face_detector = cv2.CascadeClassifier(CASCADE_PATH)
    if face_detector.empty():
        print("Failed to load Haar cascade.", file=sys.stderr)
        sys.exit(1)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Unable to open camera device.", file=sys.stderr)
        sys.exit(2)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    baseline = (0.0, 0.0)
    smoothed_view = (0.0, 0.0)

    panels = [
        (_draw_panel_content(spec.title, spec.size, spec.color), spec)
        for spec in layout
    ]

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            detected = _detect_face(gray, face_detector)
            if detected is not None:
                cx, cy, face_box = detected
                vx, vy = normalize_viewer_offset(cx, cy, w, h)
                if args.debug_face:
                    x, y, fw, fh = face_box
                    cv2.rectangle(frame, (x, y), (x + fw, y + fh), (60, 255, 180), 2)
            else:
                vx, vy = 0.0, 0.0

            vx, vy = relative_viewer_offset((vx, vy), baseline)
            smoothed_view = smooth_viewer_offset(smoothed_view, (vx, vy), smoothing)

            canvas = np.zeros_like(frame)
            canvas[:] = (16, 18, 24)

            for panel, spec in panels:
                quad = quad_from_view(
                    w * spec.center[0],
                    h * spec.center[1],
                    spec.size[0],
                    spec.size[1],
                    smoothed_view[0] * spec.scale,
                    smoothed_view[1] * spec.scale,
                    strength=spec.strength,
                )
                _warp_panel(canvas, panel, quad)
                _draw_box_frame(canvas, quad, spec.color, smoothed_view, spec.strength)

            overlay = frame.copy()
            cv2.rectangle(overlay, (10, 10), (640, 110), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.28, frame, 0.72, 0)
            cv2.putText(frame, f"Viewer offset x={smoothed_view[0]:+.2f} y={smoothed_view[1]:+.2f}", (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Layout={args.layout} smoothing={smoothing:.2f}", (20, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 230), 1, cv2.LINE_AA)
            cv2.putText(frame, "Keys: [R] reset baseline, [Q]/[ESC] quit", (20, 86), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 230), 1, cv2.LINE_AA)

            out = cv2.hconcat([frame, canvas])
            cv2.imshow("OffAxis Test (Camera | Off-axis Composite)", out)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("r"):
                baseline = (vx + baseline[0], vy + baseline[1])
                smoothed_view = (0.0, 0.0)

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
