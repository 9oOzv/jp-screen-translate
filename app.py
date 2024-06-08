#!/usr/bin/env python3
from PIL import (
    Image,
    ImageGrab,
    ImageTk
)
from pathlib import Path
from time import (
    sleep,
    time
)
import os
import pyautogui
import pytesseract
import tkinter as tk
from util import (
    first,
    on_windows,
    combine_columns,
    make_column,
    clear_tty,
    Color,
    nothing,
    merge_texts,
    scale_image,
)
from kanji_translator import KanjiTranslator
from itertools import islice
from contextlib import contextmanager
from logging import (
    getLogger,
    DEBUG,
    INFO,
)
from log import (
    configure_logger,
    TRACE
)
from command import Commands
import cProfile as profile
from pstats import SortKey

log = getLogger('app')


FWS = '　'

TESSERACT_SEARCH_PATHS = [
    Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe'),
    Path(r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'),
]

if 'TESSERACT_PATH' in os.environ:
    TESSERACT_SEARCH_PATHS.append(Path(
        os.environ['TESSERA_PATH']
    ))
    TESSERACT_SEARCH_PATHS.append(
        Path(os.environ['TESSERA_PATH']) / 'tesseract.exe'
    )


class Tooltip(tk.Tk):
    offset_x = 64
    offset_y = 64
    labels = []
    texts = []
    images = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bg = 'black'
        self.overrideredirect(True)
        self.attributes('-alpha', 0.9)
        self.attributes('-topmost', True)
        self.title("Transparent Window")
        self.configure(bg=bg)
        self.frame = tk.Frame(self, bg='black')
        self.frame.pack(anchor='w')
        self.update()

    def add(self, text, color='black'):
        log.debug({
            'message': 'Adding text to tooltip',
            'text': text,
        })
        self.texts.append({'text': text, 'color': color})

    def add_image(self, image: Image):
        log.debug({
            'message': 'Adding image to tooltip',
            'size': image.size,
        })
        self.images.append(image)

    def clear(self):
        self.texts = []
        self.images = []

    def hide(self):
        self.withdraw()

    @contextmanager
    def hidden(self):
        try:
            self.hide()
            yield
        finally:
            self.show()

    def show(self):
        self.deiconify()

    def update(self):
        for label in self.labels:
            label.pack_forget()
            label.destroy()
        for image in self.images:
            image = ImageTk.PhotoImage(image)
            label = tk.Label(self.frame, image=image)
            label.pack(anchor='w')
            self.labels.append(label)
        for text in self.texts:
            label = tk.Label(
                self.frame,
                text=text['text'],
                font=("Helvetica", 12),
                justify='left',
                bg='black',
                fg=text['color']
            )
            label.pack(anchor='w')
            self.labels.append(label)
        self.frame.pack_forget()
        self.frame.pack(anchor='w')
        x, y = pyautogui.position()
        x += self.offset_x
        y += self.offset_y
        w = self.frame.winfo_reqwidth()
        h = self.frame.winfo_reqheight()
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


class App:
    """
    Capture and translate kanji from the screen.

    Args:
        capture_size_x (int): The width of the capture region.
        capture_size_y (int): The height of the capture region.
        capture_threshold (int): The maximum distance from the last capture
            position to trigger a new capture.
        interval (float): The time in seconds to wait between captures.
        force_interval (float): The time in seconds to wait before forcing a
            new capture.
        gui (bool): Whether to show a tooltip with the translation.
        clear_tty (bool): Whether to clear terminal between prints.
        max_entries (int): The maximum number of entries to show in the
            tooltip.
        gui_colors (list[str]): The colors to use for the tooltip entries.
        debug (bool): Whether to log debug messages.
        trace (bool): Whether to log trace messages.
        profile (bool): Whether to profile the application.
        pretty (bool): Whether to use pretty printing for logs.
        capture_preview (bool): Whether to show a preview of the capture in
            the tooltip.
    """

    capture_size_x = 240
    capture_size_y = 120
    capture_offset_x = 0
    capture_offset_y = -16
    prev_capture_time = 0
    prev_capture_x = 0
    prev_capture_y = 0
    capture_threshold = 16
    interval = 0.5
    force_interval = 10.0
    _tooltip = None
    fps = 24
    gui = False
    clear_tty = False
    max_entries = 8
    gui_colors = [Color.random_hsluv(lum=75, sat=100) for _ in range(8)]
    profile = False
    pretty = False
    capture_preview = True
    preview = None

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
        gui: bool = None,
        clear_tty: bool = None,
        max_entries: int = None,
        gui_colors: list[str] = [
            Color.random_hsluv(lum=75, sat=100)
            for _ in range(8)
        ],
        debug: bool = None,
        trace: bool = None,
        profile: bool = None,
        pretty: bool = None,
        capture_preview: bool = None,
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
        self.clear_tty = clear_tty or self.clear_tty
        self.max_entries = max_entries or self.max_entries
        self.gui_colors = gui_colors or self.gui_colors
        self.profile = profile or self.profile
        self.log_level = (
            DEBUG if debug
            else TRACE if trace
            else INFO
        )
        self.pretty = pretty or self.pretty
        self.capture_preview = capture_preview or self.capture_preview
        configure_logger('app', level=self.log_level, pretty=self.pretty)
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

    def _sizes(self, img: Image):
        half = scale_image(img, 0.5)
        fourth = scale_image(img, 0.25)
        return [img, half, fourth]

    def _capture(self):
        self.prev_capture_time = time()
        self.prev_capture_x = self.x
        self.prev_capture_y = self.y
        region = (
            self.x - self.capture_size_x // 2 + self.capture_offset_x,
            self.y - self.capture_size_y // 2 + self.capture_offset_y,
            self.x + self.capture_size_x // 2 + self.capture_offset_x,
            self.y + self.capture_size_y // 2 + self.capture_offset_y,
        )
        with self.tooltip.hidden() if self.gui else nothing():
            img = ImageGrab.grab(region)
        self.captures = self._sizes(img)
        if self.capture_preview:
            self.preview = scale_image(img, max_dimension=120)
        text = merge_texts([
            pytesseract.image_to_string(
                img,
                lang='jpn',
                config='--oem 1 --psm 11'
            )
            for img in self.captures
        ])
        return KanjiTranslator.only_kanji_kana(text)


    def should_capture(self):
        self.x, self.y = pyautogui.position()
        return (
            time() > self.prev_capture_time + self.force_interval
            or not self.near_last_capture(self.x, self.y)
        )

    def next_capture(self, hide_tooltip=True):
        if self.should_capture():
            if self.gui:
                with self.tooltip.hidden():
                    return self._capture()
            else:
                return self._capture()

    def _loop(self):
        captured = self.next_capture()
        if captured is None:
            return
        self.captured = captured
        infos = self.translator.text_kanji_info(self.captured)
        self.infos = infos
        texts = []
        # limit generator output to max_entries
        for info in islice(infos, self.max_entries):
            kanji = FWS.join(info['kanji'])
            kana = FWS.join(info['kana'])
            gloss = '  '.join(info['gloss'])
            tmp_columns = [
                make_column(kanji, 4),
                make_column(kana, 6),
                make_column(gloss, 60)
            ]
            num_lines = max(
                c.count('\n') + 1
                for c in tmp_columns
            )
            text = combine_columns(
                make_column(kanji, 4, whitespace=FWS, num_lines=num_lines),
                make_column(kana, 6, whitespace=FWS, num_lines=num_lines),
                make_column(gloss, 60, num_lines=num_lines),
                separator='  '
            )
            texts.append(text)
        self.text = '\n'.join(texts)
        if self.clear_tty:
            clear_tty()
        else:
            print()
        to_print = '\n'.join([
            self.captured,
            self.text
        ])
        print(to_print)
        if self.gui:
            self.update_gui_texts([self.captured, *texts])

    def _run(self):
        self.translator = KanjiTranslator()
        try:
            while True:
                self._loop()
                self._wait()
        except KeyboardInterrupt:
            pass

    def update_gui_texts(self, texts):
        log.debug({ 'message': 'Updating GUI', 'texts': texts })
        self.tooltip.clear()
        if self.capture_preview and self.preview:
            self.tooltip.add_image(self.preview)
        for i, text in enumerate(texts):
            self.tooltip.add(
                text,
                color=self.gui_colors[i % len(self.gui_colors)]
            )
        self.tooltip.update()

    def _wait(self):
        t = 1.0 / self.fps
        for _ in range((int)(self.interval // t)):
            if self.gui:
                self.tooltip.update()
            sleep(t)

    def run(self):
        if self.profile:
            profile.runctx(
                'self._run()',
                globals(),
                locals(),
                sort=SortKey.CUMULATIVE
            )
        else:
            self._run()

    @property
    def tooltip(self):
        if not self.gui:
            return None
        if self._tooltip:
            return self._tooltip
        self._tooltip = Tooltip()
        return self._tooltip

if __name__ == "__main__":
    commands = Commands()
    commands.create(App, 'run')
    commands.alias('cli', 'run', gui=False)
    commands.alias('gui', 'run', gui=True)
    commands.fire()

