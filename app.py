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
import tkinter as tk
from capture import CaptureSet
from util import (
    first,
    on_windows,
    combine_columns,
    make_column,
    clear_tty,
    Color,
    nothing,
    merge_texts,
)
from typing import (
    Iterable,
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
import pstats
import cProfile
import numpy
from textwrap import wrap


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
    frame = None
    image_frame = None
    # Need to keep a reference to the images. Otherwise they will be garbage
    # collected or something.
    photoImages = []
    font_size: float = 12

    def __init__(
        self,
        font_size: float = 12,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.font_size = font_size
        bg = 'black'
        self.overrideredirect(True)
        self.attributes('-alpha', 0.9)
        self.attributes('-topmost', True)
        self.title("Transparent Window")
        self.configure(bg=bg)
        self.frame = tk.Frame(self, bg='black')
        self.frame.pack(anchor='w')
        self.image_frame = tk.Frame(self, bg='red')
        self.image_frame.pack(anchor='w')
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
        self.photoImages = []

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
        self.photoImages = [
            ImageTk.PhotoImage(image)
            for image in self.images
        ]
        for i, image in enumerate(self.photoImages):
            label = tk.Label(self.image_frame, image=image)
            label.grid(row=0, column=i)
            self.labels.append(label)
        for text in self.texts:
            label = tk.Label(
                self.frame,
                text=text['text'],
                font=(
                    "Helvetica",
                    self.font_size,
                ),
                justify='left',
                bg='black',
                fg=text['color']
            )
            label.pack(anchor='w')
            self.labels.append(label)
        self.image_frame.pack_forget()
        self.image_frame.pack(anchor='w')
        self.frame.pack_forget()
        self.frame.pack(anchor='w')
        x, y = pyautogui.position()
        x += self.offset_x
        y += self.offset_y
        w = max(
            self.frame.winfo_reqwidth(),
            self.image_frame.winfo_reqwidth()
        )
        h = (
            self.frame.winfo_reqheight()
            + self.image_frame.winfo_reqheight()
        )
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
        profile (bool | str): Whether to profile the code. If a string is
            provided, it will be used as the file name for the profile stats.
        pretty (bool): Whether to use pretty printing for logs.
        capture_preview (bool): Whether to show a preview of the capture in
            the tooltip.
        tesseract (bool): Whether to use Tesseract for OCR.
        easyocr (bool): Whether to use EasyOCR for OCR.
        scales (int): Number of scaled versions of the capture to use for OCR.
        divs (int): Divide capture region to multiplw parts for OCR.
        kanji_column (int): The width of the kanji column in the tooltip.
        kana_column (int): The width of the kana column in the tooltip.
        gloss_column (int): The width of the gloss column in the tooltip.
        capture_column (int): The width of the capture column in the tooltip.
        font_size (float): The font size to use in the tooltip.
    """

    capture_size_x: int = 160
    capture_size_y: int = 100
    capture_offset_x: int = 0
    capture_offset_y: int = -16
    prev_capture_time: int = 0
    prev_capture_x: int = 0
    prev_capture_y: int = 0
    capture_threshold: int = 16
    interval: float = 0.5
    force_interval: float = 10.0
    _tooltip: Tooltip = None
    fps: int = 24
    gui: bool = False
    clear_tty: bool = False
    max_entries: int = 8
    gui_colors: Iterable[Color] = [
        Color.random_hsluv(lum=75, sat=100)
        for _ in range(8)
    ]
    profile: bool | str = False
    pretty: bool = False
    capture_preview: bool = True
    pytesseract = None
    easyocr_reader = None
    tesseract: bool | None = None
    easyocr: bool | None = None
    debug: bool = False
    trace: bool = False
    scales: int = None
    divs: int = None
    kanji_column: int = 4
    kana_column: int = 6
    gloss_column: int = 60
    capture_column: int = 36
    text: str = ''
    capture_text: str = ''
    font_size: float = 11

    def __init__(
        self,
        *args,
        capture_size_x: int = capture_size_x,
        capture_size_y: int = capture_size_y,
        capture_offset_x: int = capture_offset_x,
        capture_offset_y: int = capture_offset_y,
        capture_threshold: int = capture_threshold,
        interval: float = interval,
        force_interval: float = force_interval,
        gui: bool = gui,
        clear_tty: bool = clear_tty,
        max_entries: int = max_entries,
        gui_colors: Iterable[Color] = gui_colors,
        debug: bool = debug,
        trace: bool = trace,
        profile: bool | str = profile,
        pretty: bool = pretty,
        capture_preview: bool | None = capture_preview,
        tesseract: bool | None = tesseract,
        easyocr: bool | None = easyocr,
        scales: int  | None = None,
        divs: int | None = divs,
        kanji_column: int = kanji_column,
        kana_column: int = kana_column,
        gloss_column: int = gloss_column,
        capture_column: int = capture_column,
        font_size: float = font_size,
    ):
        self.capture_size_x = capture_size_x
        self.capture_size_y = capture_size_y
        self.capture_offset_x = capture_offset_x
        self.capture_offset_y = capture_offset_y
        self.new_capture_threshold = (capture_threshold)
        self.interval = interval
        self.force_interval = force_interval
        self.gui = gui
        self.clear_tty = clear_tty
        self.max_entries = max_entries
        self.gui_colors = gui_colors
        self.profile = profile
        self.log_level = (
            TRACE
            if trace
            else DEBUG
            if debug
            else INFO
        )
        self.pretty = pretty
        self.capture_preview = capture_preview
        if tesseract:
            self.setup_tesseract()
        if easyocr:
            self.setup_easyocr()
        if not self.tesseract and not self.easyocr:
            self.auto_select_ocr()
        self.scales = scales
        self.divs = divs
        self.kanji_column = kanji_column
        self.kana_column = kana_column
        self.gloss_column = gloss_column
        self.capture_column = capture_column
        self.font_size = font_size
        configure_logger('app', level=self.log_level, pretty=self.pretty)
        configure_logger(None, level=self.log_level, pretty=self.pretty)

    def setup_easyocr(self):
        from easyocr import Reader
        self.easyocr_reader = Reader(['ja'])
        self.easyocr = True

    def setup_tesseract(self):
        import pytesseract
        self.pytesseract = pytesseract
        tesseract_exe = first([
            p for p in TESSERACT_SEARCH_PATHS
            if p.exists() and p.is_file()
        ])
        if on_windows():
            self.pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
        self.tesseract = True

    def auto_select_ocr(self):
        try:
            self.setup_easyocr()
        except ImportError:
            self.setup_tesseract()

    def near_last_capture(self, x, y):
        return (
            x >= self.prev_capture_x - self.capture_threshold
            and x <= self.prev_capture_x + self.capture_threshold
            and y >= self.prev_capture_y - self.capture_threshold
            and y <= self.prev_capture_y + self.capture_threshold
        )

    def _capture_set(self, img: Image) -> CaptureSet:
        kwargs = {}
        if self.divs:
            kwargs['auto_parts'] = (self.divs, self.divs)
        if self.scales:
            kwargs['scales'] = [
                1 / (2 ** (i))
                for i in range(self.scales)
            ]
        return CaptureSet(img, **kwargs)

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
            self.capture = self._capture_set(img)
        text = merge_texts([
            self._ocr(img)
            for img in self.capture.images()
        ])
        return text

    def _tesseract(self, img: Image):
        log.debug({
            'message': 'Running Tesseract',
            'img.size': img.size,
        })
        if not self.pytesseract:
            import pytesseract
            self.pytesseract = pytesseract
            tesseract_exe = first([
                p for p in TESSERACT_SEARCH_PATHS
                if p.exists() and p.is_file()
            ])
            if on_windows():
                self.pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
        return [
            self.pytesseract.image_to_string(
                img,
                lang='jpn',
                config=f'--psm {psm}'
            )
            for psm in [5, 6]
        ]

    def _easyocr(self, img: Image):
        log.debug({
            'message': 'Running EasyOCR',
            'img.size': img.size,
        })
        if not self.easyocr_reader:
            from easyocr import Reader
            self.easyocr_reader = Reader(['ja'])
        texts = [
            v[1]
            for v in
            self.easyocr_reader.readtext(numpy.array(img))
        ]
        return texts

    def _ocr(self, image: Image = None) -> str:
        ocrs = []
        if self.tesseract:
            ocrs.append(self._tesseract)
        if self.easyocr:
            ocrs.append(self._easyocr)
        if not ocrs:
            raise ValueError('No OCR engines enabled')
        texts = [
            t
            for ocr in ocrs
            for t in ocr(image)
        ]
        log.debug({
            'message': 'OCR results',
            'texts': texts
        })
        return merge_texts(texts)

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
        log.debug({'message': 'Loop'})
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
                make_column(kanji, self.kanji_column),
                make_column(kana, self.kana_column),
                make_column(gloss, self.gloss_column)
            ]
            num_lines = max(
                c.count('\n') + 1
                for c in tmp_columns
            )
            text = combine_columns(
                make_column(
                    kanji,
                    self.kanji_column,
                    whitespace=FWS,
                    num_lines=num_lines
                ),
                make_column(
                    kana,
                    self.kana_column,
                    whitespace=FWS,
                    num_lines=num_lines
                ),
                make_column(
                    gloss,
                    self.gloss_column,
                    num_lines=num_lines
                ),
                separator='    '
            )
            texts.append(text)
        self.text = '\n'.join(texts)
        if self.clear_tty:
            clear_tty()
        else:
            print()
        self.capture_text = '\n'.join(
            wrap(
                self.captured,
                width=(
                    self.kanji_column
                    + self.kana_column
                    + self.gloss_column
                ),
                break_long_words=True
            )
        )
        wrapped_capture = '\n'.join(
            wrap(
                self.capture_text,
                width=self.capture_column,
                break_long_words=True
            )
        )
        to_print = '\n'.join([
            wrapped_capture,
            self.text
        ])
        print(to_print)
        if self.gui:
            self.update_gui([
                wrapped_capture,
                *texts,
            ])

    def _run(self):
        self.translator = KanjiTranslator()
        try:
            while True:
                self._loop()
                self._wait()
        except KeyboardInterrupt:
            pass

    def update_gui(self, texts):
        log.debug({
            'message': 'Updating GUI',
            'texts': texts,
        })
        self.tooltip.clear()
        if self.capture_preview and self.capture:
            images = self.capture.preview()
            for img in images:
                self.tooltip.add_image(img)
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

    def _print_profile(self):
        print(
            '\n'
            .join(self._profile_lines())
        )

    def _save_profile(self):
        with open(self.profile, 'w') as f:
            f.write(
                '\n'
                .join(self._profile_lines())
            )

    def _profile_lines(self):
        stat_items = self.profile_stats.stats.items()
        stats = []
        for func, (cc, nc, tt, ct, callers) in stat_items:
            stats.append({
                'path': func[0],
                'line': func[1],
                'func': func[2],
                'stdname': cc,
                'calls': nc,
                'time': tt,
                'cumulative': ct,
            })
        stats = sorted(
            stats,
            key=lambda x: x['cumulative'],
            reverse=True
        )

        def statline(s):
            filename = Path(s['path']).name
            cols = [
                f'{filename:20.20}',
                f'{str(s["line"]):4.4}',
                f'{s["func"]:20.20}',
                f'{s["cumulative"]:.3f} seconds',
            ]
            return '  '.join(cols)

        return [
            statline(s)
            for s in stats
        ]

    def _run_profile(self):
        with cProfile.Profile() as profiler:
            self._run()
        self.profile_stats = pstats.Stats(profiler)
        if self.profile is True:
            self._print_profile()
        else:
            self._save_profile()

    def run(self):
        if self.profile:
            self._run_profile()
        else:
            self._run()

    @property
    def tooltip(self):
        if not self.gui:
            return None
        if self._tooltip:
            return self._tooltip
        self._tooltip = Tooltip(font_size=self.font_size)
        return self._tooltip


if __name__ == "__main__":
    commands = Commands()
    commands.create(App, 'run')
    commands.alias('cli', 'run', gui=False)
    commands.alias('gui', 'run', gui=True)
    commands.fire()

