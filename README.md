# snapcap

A Windows screenshot utility designed for automatically saving timestamped images with optional prefixes.

Can capture the active window, the full screen, or an ad-hoc rectangle.

Designed for optimal use with a Stream Deck or similar macro utility that can provide one-click access to different command-line features.

## Features

- Capture the active window, the full screen, or a user-drawn rectangle (multi-monitor aware)
- Timestamped filenames
- Specify an optional prefix on filenames to separate different image series
- Notification options: toast, toast with thumbnail, beep, or silent
- Click the toast to open the screenshot; auto-dismisses after a couple seconds
- Simple `config.toml` for persistent settings

## Requirements

- OS: Windows
- Python 3.11+ (for `tomllib`)
- [Pillow](https://pypi.org/project/Pillow/)

## Setup

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/#pypi)

2. Run the following commands:

```bash
uv sync
python snapcap.py --init
```

## Usage

Take a screenshot using current config:

```bash
python snapcap.py
```

### Filename prefixes

Organize different screenshot series by setting a prefix that gets prepended to all future filenames (e.g. `bugreport_2026-04-07_12-30-00-123.png`). Useful for grouping captures by project, task, or session.

To be prompted for a new prefix that will be reused for all subsequent captures until changed, add the `--prompt-prefix` argument:

```bash
python snapcap.py --prompt-prefix
```

Leave the prompt blank to disable the prefix. You can also edit `filename_prefix` directly in `config.toml`.

### Configure

```bash
python snapcap.py --output-folder C:\screenshots
python snapcap.py --capture-mode window         # window | screen | rect
python snapcap.py --notification-mode toast     # toast | toast_thumbnail | beep | none
```

Config-changing flags do not take a screenshot.

### Rectangle capture

With `capture_mode = 'rect'`, snapcap dims the screen and lets you drag out a selection rectangle with the mouse. Release the mouse button to capture it, or press Escape to cancel.

## Config

`config.toml`:

```toml
output_folder = 'C:\screenshots'
capture_mode = 'window'
notification_mode = 'toast'
filename_prefix = ''
```

## Roadmap

- Optional ability to copy the image to the clipboard, either exclusively or in addition to saving to disk.
- Support for Linux and macOS
