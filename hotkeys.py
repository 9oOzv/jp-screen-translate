from pynput import keyboard
from contextlib import contextmanager


@contextmanager
def hotkeys(controller):
    with keyboard.GlobalHotKeys({
        '<ctrl>+<shift>+<alt>+s': controller.capture,
        '<ctrl>+<shift>+<alt>+q': controller.exit,
        '<ctrl>+<shift>+<alt>+h': controller.toggle_tooltip
    }) as h:
        yield h
