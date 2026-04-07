import os
import argparse
import ctypes
import datetime
import tomllib
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

from PIL import Image, ImageEnhance, ImageGrab, ImageTk

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


def select_rect_interactively(full_image):
    """Show a dimmed fullscreen overlay and let the user drag-select a rectangle.

    Returns (left, top, right, bottom) in `full_image` pixel coordinates, or
    None if the user cancels (Escape) or makes a zero-size selection.
    """
    # Virtual screen origin — needed because ImageGrab(all_screens=True) returns
    # an image whose (0,0) is the top-left of the virtual screen, which can be
    # negative on multi-monitor setups, while Tk fullscreen uses primary screen.
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    gsm = ctypes.windll.user32.GetSystemMetrics
    vx, vy = gsm(SM_XVIRTUALSCREEN), gsm(SM_YVIRTUALSCREEN)
    vw, vh = gsm(SM_CXVIRTUALSCREEN), gsm(SM_CYVIRTUALSCREEN)

    dimmed = ImageEnhance.Brightness(full_image).enhance(0.5)

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.geometry(f"{vw}x{vh}+{vx}+{vy}")
    root.config(cursor="crosshair")

    canvas = tk.Canvas(root, width=vw, height=vh, highlightthickness=0, bd=0)
    canvas.pack()

    dim_photo = ImageTk.PhotoImage(dimmed)
    canvas.create_image(0, 0, anchor="nw", image=dim_photo)

    state = {"start": None, "rect_id": None, "img_id": None, "photo": None, "result": None}

    def on_press(event):
        state["start"] = (event.x, event.y)

    def on_drag(event):
        if state["start"] is None:
            return
        x0, y0 = state["start"]
        x1, y1 = event.x, event.y
        lx, rx = sorted((x0, x1))
        ty, by = sorted((y0, y1))
        if state["img_id"] is not None:
            canvas.delete(state["img_id"])
            state["img_id"] = None
        if rx > lx and by > ty:
            crop = full_image.crop((lx, ty, rx, by))
            photo = ImageTk.PhotoImage(crop)
            state["photo"] = photo  # keep reference
            state["img_id"] = canvas.create_image(lx, ty, anchor="nw", image=photo)
        if state["rect_id"] is None:
            state["rect_id"] = canvas.create_rectangle(lx, ty, rx, by, outline="white", width=1)
        else:
            canvas.coords(state["rect_id"], lx, ty, rx, by)
        canvas.tag_raise(state["rect_id"])

    def on_release(event):
        if state["start"] is None:
            root.destroy()
            return
        x0, y0 = state["start"]
        x1, y1 = event.x, event.y
        lx, rx = sorted((x0, x1))
        ty, by = sorted((y0, y1))
        if rx > lx and by > ty:
            state["result"] = (lx, ty, rx, by)
        root.destroy()

    def on_escape(event):
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    root.mainloop()
    return state["result"]


def capture_screenshot(capture_mode="window"):
    """Capture the active window or full screen and return a PIL Image."""
    if capture_mode == "rect":
        full = ImageGrab.grab(bbox=None, all_screens=True)
        rect = select_rect_interactively(full)
        if rect is None:
            return None
        return full.crop(rect)
    # bbox=None tells ImageGrab to capture the full virtual screen
    bbox = get_active_window_rect() if capture_mode == "window" else None
    # all_screens=True ensures multi-monitor setups are handled correctly
    return ImageGrab.grab(bbox=bbox, all_screens=True)


def save_screenshot(image, output_folder, filename_prefix=""):
    """Save the image as a timestamped PNG and return the full path."""
    os.makedirs(output_folder, exist_ok=True)

    # Timestamp format: YYYY-MM-DD_HH-MM-SS-sss
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S-") + f"{now.microsecond // 1000:03d}"
    filename = f"{filename_prefix}_{timestamp}.png" if filename_prefix else f"{timestamp}.png"
    filepath = os.path.join(output_folder, filename)

    image.save(filepath, format="PNG")
    return filepath


def show_toast(filepath, duration_ms=2000, position="bottom", thumbnail=False):
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
    root.attributes("-alpha", 1.00)    # no transparency

    filename = os.path.basename(filepath)

    def open_and_dismiss():
        os.startfile(filepath)
        root.destroy()

    btn_kwargs = dict(
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
    text = f"\u2714  Screenshot saved \u2014 {filename}"
    if thumbnail:
        img = Image.open(filepath)
        img.thumbnail((192, 192))
        photo = ImageTk.PhotoImage(img)
        btn = tk.Button(root, text=text, image=photo, compound="left", **btn_kwargs)
        btn.image = photo  # keep reference
    else:
        btn = tk.Button(root, text=text, **btn_kwargs)
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
    # Single-quoted TOML strings are literal — backslashes (e.g. Windows paths)
    # are written as-is, so values must not contain single quotes.
    lines = [f"{k} = '{v}'" for k, v in config.items()]
    CONFIG_PATH.write_text("\n".join(lines) + "\n")


def set_output_folder(folder):
    update_config(output_folder=folder)


def set_capture_mode(mode):
    update_config(capture_mode=mode)


def set_notification_mode(mode):
    update_config(notification_mode=mode)


def set_filename_prefix(prefix):
    update_config(filename_prefix=prefix)


def prompt_filename_prefix(default=""):
    """Show a small modal asking the user for a new filename prefix."""
    from tkinter import simpledialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    result = simpledialog.askstring(
        "snapcap", "Filename prefix:", initialvalue=default, parent=root
    )
    root.destroy()
    return result if result is not None else default


def play_beep():
    import winsound
    winsound.Beep(1000, 150)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-folder")
    parser.add_argument("--capture-mode", choices=["window", "screen", "rect"])
    parser.add_argument(
        "--notification-mode",
        choices=["toast", "toast_thumbnail", "beep", "none"],
    )
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--prompt-prefix", action="store_true")
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

    # Config-changing args suppress the screenshot; otherwise capture as normal.
    if not config_changed:
        if not CONFIG_PATH.exists():
            contents = init_config()
            print(f"No config found. Initialized config.toml with:\n{contents}")
        config = load_config()
        # Capture first so the prompt dialog doesn't appear in the screenshot.
        image = capture_screenshot(config.get("capture_mode", "window"))
        if image is None:
            print("Capture cancelled.")
            raise SystemExit(0)
        prefix = config.get("filename_prefix", "")
        if args.prompt_prefix:
            prefix = prompt_filename_prefix(default=prefix)
            set_filename_prefix(prefix)
        saved_to = save_screenshot(image, config["output_folder"], prefix)
        print(f"Screenshot saved: {saved_to}")
        notification_mode = config.get("notification_mode", "toast")
        if notification_mode == "beep":
            play_beep()
        elif notification_mode == "toast":
            show_toast(saved_to)
        elif notification_mode == "toast_thumbnail":
            show_toast(saved_to, thumbnail=True)

