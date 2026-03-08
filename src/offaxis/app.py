"""Camera-based OffAxis prototype app."""

from __future__ import annotations

import sys
from typing import Optional

import cv2
import numpy as np

from .projection import normalize_viewer_offset, quad_from_view


CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


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


def _detect_face_center(gray: np.ndarray, face_detector: cv2.CascadeClassifier) -> Optional[tuple[float, float]]:
    faces = face_detector.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return x + w / 2.0, y + h / 2.0


def main() -> None:
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

    panel_a = _draw_panel_content("Screen A", (460, 300), (60, 190, 255))
    panel_b = _draw_panel_content("Screen B", (420, 260), (140, 100, 255))
    panel_c = _draw_panel_content("Screen C", (360, 220), (60, 220, 160))

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            detected_center = _detect_face_center(gray, face_detector)
            if detected_center is not None:
                vx, vy = normalize_viewer_offset(detected_center[0], detected_center[1], w, h)
            else:
                vx, vy = 0.0, 0.0

            vx -= baseline[0]
            vy -= baseline[1]

            vx = max(-1.0, min(1.0, vx))
            vy = max(-1.0, min(1.0, vy))

            canvas = np.zeros_like(frame)
            canvas[:] = (16, 18, 24)

            quad_a = quad_from_view(w * 0.35, h * 0.52, 460, 300, vx, vy, strength=0.18)
            quad_b = quad_from_view(w * 0.68, h * 0.44, 420, 260, vx * 0.75, vy * 0.75, strength=0.22)
            quad_c = quad_from_view(w * 0.62, h * 0.72, 360, 220, vx * 0.55, vy * 0.55, strength=0.15)

            _warp_panel(canvas, panel_a, quad_a)
            _warp_panel(canvas, panel_b, quad_b)
            _warp_panel(canvas, panel_c, quad_c)

            overlay = frame.copy()
            cv2.rectangle(overlay, (10, 10), (420, 88), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.28, frame, 0.72, 0)
            cv2.putText(frame, f"Viewer offset x={vx:+.2f} y={vy:+.2f}", (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, "Keys: [R] reset baseline, [Q]/[ESC] quit", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 230), 1, cv2.LINE_AA)

            out = cv2.hconcat([frame, canvas])
            cv2.imshow("OffAxis Test (Camera | Off-axis Composite)", out)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("r"):
                baseline = (vx + baseline[0], vy + baseline[1])

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
