from fire import Fire
from PIL import ImageGrab
from pathlib import Path
from time import (
    sleep,
    time
)
import inspect
import jamdict
import os
import pyautogui
import pytesseract
import re
from util import (
    first,
    on_windows,
    all_substrings,
    clear,
    strings,
    combine_columns,
    make_column
)
import tkinter as tk


FWS = '　'

TESSERACT_SEARCH_PATHS = [
    Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe'),
    Path(r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'),
]

if 'TESSERACT_PATH' in os.environ:
    TESSERACT_SEARCH_PATHS.append(Path(os.environ['TESSERA_PATH']))
    TESSERACT_SEARCH_PATHS.append(Path(os.environ['TESSERA_PATH']) / 'tesseract.exe')


class TkTooltip(tk.Tk):
    offset_x = 64
    offset_y = 64

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bg = 'black'
        fg = 'white'
        self.overrideredirect(True)
        self.attributes('-alpha', 0.9)
        self.attributes('-topmost', True)
        self.title("Transparent Window")
        self.configure(bg=bg)
        self.label = tk.Label(
            self,
            text='Nothing here',
            font=("Helvetica", 12),
            justify='left',
            bg=bg,
            fg=fg
        )
        self.update()

    def set_text(self, text):
        self.label.config(text=text)
        self.label.pack(anchor='w')
        self.update()

    def update(self):
        x, y = pyautogui.position()
        x += self.offset_x
        y += self.offset_y
        w = self.label.winfo_reqwidth()
        h = self.label.winfo_reqheight()
        # Make sure the window is not outside the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        if x + w > screen_width:
            x -= w + 2 * self.offset_x
        if y + h > screen_height:
            y -= h + 2 * self.offset_y
        self.geometry(f'{w}x{h}+{x}+{y}')
        super().update()
        super().update_idletasks()


class KanjiTranslator:

    def __init__(self):
        self.jam = jamdict.Jamdict()

    @staticmethod
    def _jdm_entry_to_dict(entry):
        return {
            'kanji': strings(entry.kanji_forms),
            'kana': strings(entry.kana_forms),
            'gloss': [
                g for sense in entry.senses
                for g in strings(sense.gloss)
            ]
        }

    @staticmethod
    def find_kanji_sequences(text):
        return (
            s
            for part in re.split(r'[^一-龯]{2,}', text)
            if re.match(r'[一-龯]', part)
            for s in all_substrings(part)
        )

    def kanji_info(self, kanji):
        entries = self.jam.lookup(kanji).entries or []
        return (
            self._jdm_entry_to_dict(entry)
            for entry in entries
        )

    def text_kanji_info(self, text):
        kanji_sequences = sorted(
            self.find_kanji_sequences(text),
            key=len,
        )
        return (
            info
            for kanji in kanji_sequences
            for info in self.kanji_info(kanji)
        )


class App:
    """
    Capture and translate kanji from the screen.

    Args:
        capture_size_x (int): The width of the capture region.
        capture_size_y (int): The height of the capture region.
        capture_threshold (int): The maximum distance from the last capture position to trigger a new capture.
        interval (float): The time in seconds to wait between captures.
    """

    capture_size_x = 128
    capture_size_y = 64
    capture_offset_x = 0
    capture_offset_y = -16
    prev_capture_time = 0
    prev_capture_x = 0
    prev_capture_y = 0
    capture_threshold = 16
    interval = 0.5
    force_interval = 2.0
    _tooltip = None
    fps = 24
    gui = False

    def __init__(
        self,
        *args,
        capture_size_x: int = None,
        capture_size_y: int = None,
        capture_offset_x: int = None,
        capture_offset_y: int = None,
        capture_threshold: int = None,
        interval: float = None,
        force_interval: float = None,
        gui: bool = None
    ):
        self.capture_size_x = capture_size_x or self.capture_size_x
        self.capture_size_y = capture_size_y or self.capture_size_y
        self.capture_offset_x = capture_offset_x or self.capture_offset_x
        self.capture_offset_y = capture_offset_y or self.capture_offset_y
        self.new_capture_threshold = (
                capture_threshold
                or self.capture_threshold
        )
        self.interval = interval or self.interval
        self.force_interval = force_interval or self.force_interval
        self.gui = gui or self.gui
        self.setup_tesseract()

    @staticmethod
    def setup_tesseract():
        tesseract_exe = first([
            p for p in TESSERACT_SEARCH_PATHS
            if p.exists() and p.is_file()
        ])
        if on_windows():
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)

    def near_last_capture(self, x, y):
        return (
            x >= self.prev_capture_x - self.capture_threshold
            and x <= self.prev_capture_x + self.capture_threshold
            and y >= self.prev_capture_y - self.capture_threshold
            and y <= self.prev_capture_y + self.capture_threshold
        )

    def next_capture(self):
        x, y = pyautogui.position()
        should_capture = (
            time() > self.prev_capture_time + self.force_interval
            or not self.near_last_capture(x, y)
        )
        if not should_capture:
            return
        self.prev_capture_time = time()
        self.prev_capture_x = x
        self.prev_capture_y = y
        region = (
            x - self.capture_size_x // 2 + self.capture_offset_x,
            y - self.capture_size_y // 2 + self.capture_offset_y,
            x + self.capture_size_x // 2 + self.capture_offset_x,
            y + self.capture_size_y // 2 + self.capture_offset_y,
        )
        screenshot = ImageGrab.grab(region)
        text = pytesseract.image_to_string(screenshot, lang='jpn')
        return text

    def _run(self):
        text = self.next_capture()
        if text is None:
            return
        translator = KanjiTranslator()
        translations = translator.text_kanji_info(text)
        texts = []
        for t in translations:
            kanji = FWS.join(t['kanji'])
            kana = FWS.join(t['kana'])
            glosses = '  '.join(t['gloss'])
            tmp_columns = [
                make_column(kanji, 4),
                make_column(kana, 6),
                make_column(glosses, 60)
            ]
            num_lines = max(
                c.count('\n') + 1
                for c in tmp_columns
            )
            text = combine_columns(
                make_column(kanji, 4, whitespace=FWS, num_lines=num_lines),
                make_column(kana, 6, whitespace=FWS, num_lines=num_lines),
                make_column(glosses, 60, num_lines=num_lines),
                separator='  '
            )
            texts.append(text)
        self.text = '\n'.join(texts)
        print(self.text)
        if self.gui:
            self.tooltip.set_text(text)

    def _wait(self):
        t = 1.0 / self.fps
        for _ in range((int)(self.interval // t)):
            if self.gui:
                self.tooltip.update()
            sleep(t)

    def run(self):
        try:
            while True:
                self._run()
                self._wait()
        except KeyboardInterrupt:
            pass

    @property
    def tooltip(self):
        if not self.gui:
            return None
        if self._tooltip:
            return self._tooltip
        self._tooltip = TkTooltip()
        return self._tooltip


def cli(*args, **kwargs):
    if 'force_interval' not in kwargs:
        kwargs['force_interval'] = 30.0
    app = App(*args, **kwargs)
    return app.run()


cli.__doc__ = inspect.getdoc(App)
cli.__signature__ = inspect.signature(App)


def gui(*args, **kwargs):
    if 'gui' not in kwargs:
        kwargs['gui'] = True
    app = App(*args, **kwargs)
    return app.run()


gui.__doc__ = inspect.getdoc(App)
gui.__signature__ = inspect.signature(App)


commands = {
    'cli': cli,
    'gui': gui,
    'help': lambda: Fire(commands, command='--help'),
}

if __name__ == "__main__":
    Fire(commands)
