# snapcap

A lightweight Windows screenshot utility. Captures the active window (or full screen), saves it as a timestamped PNG, and shows a clickable toast notification.

## Features

- Capture the active window or the full virtual screen (multi-monitor aware)
- Timestamped filenames with optional prefix
- Notification options: toast, toast with thumbnail, beep, or silent
- Click the toast to open the screenshot; auto-dismisses after a couple seconds
- Simple `config.toml` for persistent settings

## Requirements

- Windows (uses `ctypes`/`winsound`/`os.startfile`)
- Python 3.11+ (for `tomllib`)
- [Pillow](https://pypi.org/project/Pillow/)

## Setup

```bash
uv sync
python snapcap.py --init
```

`--init` copies `config.toml.example` to `config.toml`.

## Usage

Take a screenshot using current config:

```bash
python snapcap.py
```

### Filename prefixes

Organize different screenshot series by setting a prefix that gets prepended to all future capture filenames (e.g. `bugreport_2026-04-07_12-30-00-123.png`). Useful for grouping captures by project, task, or session.

Be prompted for a new prefix at capture time — the value is saved to `config.toml` and reused for all subsequent captures until changed:

```bash
python snapcap.py --prompt-prefix
```

Leave the prompt blank to disable the prefix. You can also edit `filename_prefix` directly in `config.toml`.

### Configure

```bash
python snapcap.py --output-folder C:\screenshots
python snapcap.py --capture-mode window         # or: screen
python snapcap.py --notification-mode toast     # toast | toast_thumbnail | beep | none
```

Config-changing flags do not take a screenshot.

## Config

`config.toml`:

```toml
output_folder = 'C:\screenshots'
capture_mode = 'window'
notification_mode = 'toast'
filename_prefix = ''
```
