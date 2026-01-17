# Minesweeper (Pi + Desktop)

A Pygame-based Minesweeper that can run on a Raspberry Pi with GPIO buttons or on a laptop/desktop using keyboard input.

## Features
- Cross-platform input handling (GPIO buttons on Pi, keyboard on desktop)
- Event-driven architecture with views and an asset manager
- Auto-Solver with optional AI debug visualization via `--ai-debug`

## Requirements
- Python 3.10+
- Pygame
- Raspberry Pi only: RPi.GPIO

## Running
From the `src` folder:
```bash
python main.py EN 10
# Or:
python main.py DE 10 --ai-debug
```
Arguments:
- LANGUAGE: `EN` or `DE`
- MINECOUNT: integer >= 10
- Optional: `--ai-debug` (`--ai`, `ai`, `debug`)

## Cross-Platform Input
- On Raspberry Pi:
  - Uses `RPi.GPIO` in BCM mode and polls pins mapped in `input.py`.
- On desktop:
  - Uses Pygame keyboard events mapped via `config.KEY_EVENT_MAP`.

If you are not on a Pi, ensure a GPIO mock exists so imports succeed:

## Files Overview
- `main.py`: Entry point, argument parsing, display init, main loop.
- `input.py`: EventManager for keyboard and GPIO; produces Events.
- `events.py`: Enum of all game events (e.g., BUTTON_LEFT, QUIT).
- `views/`: UI screens (StartView, GameView, etc.).
- `assets.py`: AssetManager for images/fonts/strings.
- `config.py`: Constants like screen size, colors, key-event map.
- `render(...)`: Writes to framebuffer on Pi; updates Pygame window on desktop.

## Controls (desktop)
- Keyboard keys mapped in `config.KEY_EVENT_MAP`. Typical mappings include arrows, Enter, and a flag key. Adjust in `config.py` as needed.

