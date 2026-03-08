# OffAxis

OffAxis is a **test-version prototype** for a MacBook Pro 14" (Apple Silicon, including M5-class devices) that demonstrates off-axis projection of multiple virtual screens into a single display surface using the device camera.

This prototype:
- Reads live camera feed
- Tracks viewer position from face location (OpenCV Haar cascade)
- Computes a simple off-axis perspective transform
- Draws multiple virtual screen instances with parallax/perspective shift
- Supports smoothing + layout presets for better usability
- Uses **one-click launch scripts** (no global install required)

## macOS (Apple Silicon) quick start

### 1) One-click launch
Double-click:
- `scripts/launch_offaxis.command`

or run from terminal:
```bash
./scripts/launch_offaxis.command
```

What it does automatically:
- Creates local runtime env at `./.offaxis-venv` (first run)
- Installs required dependencies into that local env
- Launches `offaxis.app`

### 2) Controls
- `Q` or `Esc` = quit
- `R` = reset calibration baseline

### 3) Optional CLI flags
After activating env, you can run directly:
```bash
PYTHONPATH=src python -m offaxis.app --layout focus --smoothing 0.45 --debug-face
```

Available options:
- `--layout {default,focus}`: choose panel arrangement preset
- `--smoothing 0..1`: stabilize head-tracking jitter (higher = more responsive)
- `--debug-face`: draw detected face box in camera view

## Reset / remove local runtime
Double-click:
- `scripts/reset_offaxis.command`

or run:
```bash
./scripts/reset_offaxis.command
```

This removes:
- `./.offaxis-venv`

## Notes for MacBook Pro 14" (M5 target)

- If camera permissions are denied, allow Terminal (or the app used to launch the script) in:
  - **System Settings → Privacy & Security → Camera**
- This is an MVP validation build; production versions should use robust head-pose tracking + full calibration.

## Development

Run unit tests:
```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
