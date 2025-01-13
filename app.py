#!/usr/bin/env python3
from PIL import (
    Image,
    ImageGrab,
)
from time import time
import pyautogui
from capture import CaptureSet
from util import (
    clear_tty,
    nothing,
)
from kanji_translator import KanjiTranslator
from app_config import AppConfig
from functools import wraps
from pyutils8ccr.log import (
    log,
)
from ocr import OCR
from easyocr_ocr import EasyOCR
from tesseract_ocr import TesseractOCR
from openai_ocr import OpenAIOCR
import asyncio
import sys
from tooltip import Tooltip
from functools import cached_property
from cli_formatter import CliFormatter
from tooltip_formatter import TooltipFormatter


FWS = '　'


class App:
    prev_capture_time: int = 0
    prev_capture_x: int = 0
    prev_capture_y: int = 0
    backends: OCR = None
    capture_set: CaptureSet = None
    capture_text: str = ''
    infos = []
    last_gui_lines = None
    exit = False
    translator = None
    tooltip_formatter = None
    cli_formatter = None

    def __init__(self, config: AppConfig):
        self.configure(config)

    @wraps(AppConfig.create)
    def configure(self, config: AppConfig) -> 'App':
        self.config = config
        self.c = config
        self.tooltip_formatter = TooltipFormatter(
            self.c.max_entries,
            self.c.kanji_column,
            self.c.kana_column,
            self.c.gloss_column,
        )
        self.cli_formatter = CliFormatter(
            self.c.max_entries,
            self.c.kanji_column,
            self.c.kana_column,
            self.c.gloss_column,
        )
        log.setLevel(self.c.log_level)
        backend_classes = {
            'tesseract': TesseractOCR,
            'easyocr': EasyOCR,
            'openai': lambda: OpenAIOCR(self.c.openai_api_key)
        }
        self.backends = [
            backend_classes[b]()
            for b in self.c.backends
        ]
        return self

    def near_last_capture(self, x, y):
        return (
            x >= self.prev_capture_x - self.c.capture_threshold
            and x <= self.prev_capture_x + self.c.capture_threshold
            and y >= self.prev_capture_y - self.c.capture_threshold
            and y <= self.prev_capture_y + self.c.capture_threshold
        )

    def _capture_set(self, img: Image) -> CaptureSet:
        kwargs = {}
        if self.c.divs:
            kwargs['auto_parts'] = (self.c.divs, self.c.divs)
        if self.c.scales:
            kwargs['scales'] = [
                1 / (2 ** (i))
                for i in range(self.c.scales)
            ]
        return CaptureSet(img, **kwargs)

    async def _ocr(self, image: Image = None) -> str:
        if len(self.backends) == 0:
            log.warning('No OCR backends enabled')
        texts = [
            t
            for b in self.backends
            for t in await b.ocr(image)
        ]
        log.debug({
            'message': 'OCR results',
            'texts': texts
        })
        return ''.join(texts)

    def _should_capture(self):
        if not self.c.auto_capture:
            return False
        x, y = pyautogui.position()
        if time() < self.prev_capture_time + self.c.interval:
            return False
        if time() > self.prev_capture_time + self.c.force_interval:
            return True
        if not self.near_last_capture(x, y):
            return True

    async def capture(self):
        self.prev_capture_time = time()
        x, y = pyautogui.position()
        log.debug({
            'message': 'Capturing',
            'x': x,
            'y': y,
        })
        self.prev_capture_x = x
        self.prev_capture_y = y
        region = (
            x - self.c.capture_size_x // 2 + self.c.capture_offset_x,
            y - self.c.capture_size_y // 2 + self.c.capture_offset_y,
            x + self.c.capture_size_x // 2 + self.c.capture_offset_x,
            y + self.c.capture_size_y // 2 + self.c.capture_offset_y,
        )
        with self.tooltip.hidden() if self.c.gui else nothing():
            img = ImageGrab.grab(region)
            self.capture_set = self._capture_set(img)
        text = ''.join([
            await self._ocr(img)
            for img in self.capture_set.images()
        ])
        self.capture_text = text

    async def translate(self):
        t = self.translator
        self.infos = t.text_kanji_info(self.capture_text)

    async def format(self):
        self.cli_formatter.format(
            self.capture_text,
            self.infos
        )
        self.tooltip_formatter.format(
            self.capture_text,
            self.infos
        )

    async def capture_loop(self):
        if self._should_capture():
            await self.capture()
            await self.translate()
        await asyncio.sleep(1 / self.c.fps)

    async def cli_loop(self):
        await self.update_cli()
        await asyncio.sleep(self.c.cli_update_interval)

    async def gui_loop(self):
        if self.c.gui:
            await self.update_gui()
        await asyncio.sleep(1 / self.c.fps)

    async def _loop(self, f):
        try:
            while not self.exit:
                await f()
        except Exception as e:
            log.error({
                'message': 'Error',
                'error': e,
            }, exc_info=e)
            self.exit = True

    async def loops(self):
        await asyncio.gather(
            self._loop(self.capture_loop),
            self._loop(self.cli_loop),
            self._loop(self.gui_loop),
        )

    async def start(self):
        self.loop = asyncio.get_running_loop()
        self.translator = KanjiTranslator()
        try:
            await self.loops()
        except KeyboardInterrupt:
            sys.exit(0)

    async def update_cli(self):
        print(self.cli_formatter.text)

    async def update_gui(self):
        formatter = self.tooltip_formatter
        if self.last_gui_lines is formatter.lines:
            self.tooltip.update_position()
            return
        log.debug({
            'message': 'Updating GUI content',
            'lines': formatter.lines,
        })
        self.tooltip.clear()
        if self.c.capture_preview and self.capture_set:
            images = self.capture_set.preview()
            for img in images:
                self.tooltip.add_image(img)
        colors = self.c.gui_colors
        for i, text in enumerate(formatter.lines):
            color = colors[i % len(colors)]
            self.tooltip.add(text, color)
        self.tooltip.update()
        self.last_gui_lines = formatter.lines

    @cached_property
    def tooltip(self):
        if not self.c.gui:
            return None
        return Tooltip(font_size=self.c.font_size)
