import os
import argparse
import ctypes
import datetime
import tomllib
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

from PIL import ImageGrab

CONFIG_PATH = Path(__file__).resolve().parent / "config.toml"


def load_config():
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def get_active_window_rect():
    """Return (left, top, right, bottom) of the currently active window."""
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    if not hwnd:
        raise RuntimeError("No active window found.")

    rect = wintypes.RECT()
    if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("Could not retrieve window bounds.")

    return rect.left, rect.top, rect.right, rect.bottom


def take_screenshot(output_folder, capture_mode="window"):
    """
    Capture the active window or full screen and save it as a timestamped PNG.
    Returns the full path of the saved file.
    """
    os.makedirs(output_folder, exist_ok=True)

    bbox = get_active_window_rect() if capture_mode == "window" else None

    # Timestamp format: YYYY-MM-DD_HH-MM-SS-sss
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S-") + f"{now.microsecond // 1000:03d}"
    filename = f"{timestamp}.png"
    filepath = os.path.join(output_folder, filename)

    screenshot = ImageGrab.grab(bbox=bbox, all_screens=True)
    screenshot.save(filepath, format="PNG")

    return filepath


def show_toast(filepath, duration_ms=2000, position="bottom"):
    """
    Show a small auto-dismissing notification banner.
    Clicking it opens the screenshot; it dismisses itself after duration_ms.

    Args:
        filepath:    Full path to the saved screenshot.
        duration_ms: How long to show it before auto-dismissing (milliseconds).
        position:    "bottom" or "top" of the screen.
    """
    root = tk.Tk()
    root.overrideredirect(True)        # no title bar / borders
    root.attributes("-topmost", True)  # always on top
    root.attributes("-alpha", 0.88)    # slight transparency

    filename = os.path.basename(filepath)

    def open_and_dismiss():
        os.startfile(filepath)
        root.destroy()

    btn = tk.Button(
        root,
        text=f"\u2714  Screenshot saved \u2014 {filename}",
        command=open_and_dismiss,
        bg="#1e1e1e",
        fg="#ffffff",
        activebackground="#2d6a4f",
        activeforeground="#ffffff",
        font=("Segoe UI", 10),
        padx=18,
        pady=10,
        bd=0,
        cursor="hand2",
        relief="flat",
    )
    btn.pack()

    root.update_idletasks()            # compute widget size

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w    = root.winfo_reqwidth()
    win_h    = root.winfo_reqheight()

    x = (screen_w - win_w) // 2
    y = screen_h - win_h - 48 if position == "bottom" else 48

    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    root.after(duration_ms, root.destroy)
    root.mainloop()


def init_config():
    """Copy config.toml.example to config.toml and return its contents."""
    example = CONFIG_PATH.with_suffix(".toml.example")
    contents = example.read_text()
    CONFIG_PATH.write_text(contents)
    return contents


def update_config(**updates):
    """Update keys in config.toml, preserving other values."""
    config = load_config() if CONFIG_PATH.exists() else {}
    config.update(updates)
    lines = [f"{k} = '{v}'" for k, v in config.items()]
    CONFIG_PATH.write_text("\n".join(lines) + "\n")


def set_output_folder(folder):
    update_config(output_folder=folder)


def set_capture_mode(mode):
    update_config(capture_mode=mode)


def set_notification_mode(mode):
    update_config(notification_mode=mode)


def play_beep():
    import winsound
    winsound.Beep(1000, 200)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-folder")
    parser.add_argument("--capture-mode", choices=["window", "screen"])
    parser.add_argument("--notification-mode", choices=["toast", "beep"])
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()

    config_changed = False
    if args.init:
        contents = init_config()
        print(f"Script configured with:\n{contents}")
        config_changed = True
    if args.output_folder:
        set_output_folder(args.output_folder)
        print(f"output folder set to: {args.output_folder}")
        config_changed = True
    if args.capture_mode:
        set_capture_mode(args.capture_mode)
        print(f"capture mode set to: {args.capture_mode}")
        config_changed = True
    if args.notification_mode:
        set_notification_mode(args.notification_mode)
        print(f"notification mode set to: {args.notification_mode}")
        config_changed = True

    if not config_changed:
        if not CONFIG_PATH.exists():
            contents = init_config()
            print(f"No config found. Initialized config.toml with:\n{contents}")
        config = load_config()
        saved_to = take_screenshot(
            config["output_folder"], config.get("capture_mode", "window")
        )
        print(f"Screenshot saved: {saved_to}")
        if config.get("notification_mode", "toast") == "beep":
            play_beep()
        else:
            show_toast(saved_to)

