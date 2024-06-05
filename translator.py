from PIL import ImageGrab
from pathlib import Path
from pykakasi import kakasi
import pytesseract
from time import sleep
import jamdict
import os
import pyautogui
import re
from dataclasses import dataclass

FWS = '　'
TESSERACT_SEARCH_PATHS = [
    Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe'),
    Path(r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'),
]

if 'TESSERACT_PATH' in os.environ:
    TESSERACT_SEARCH_PATHS.append(Path(os.environ['TESSERA_PATH']))
    TESSERACT_SEARCH_PATHS.append(Path(os.environ['TESSERA_PATH']) / 'tesseract.exe')


jam = jamdict.Jamdict()
kks = kakasi()


@dataclass
class XY:
    x: int
    y: int


capture_size = XY(128, 64)
prev_capture = XY(0, 0)
new_capture_threshold = 16


def first(iterable):
    return next(iter(iterable), None)


def on_windows():
    return os.name == 'nt'


def setup_tesseract():
    tesseract_exe = first([
        p for p in TESSERACT_SEARCH_PATHS
        if p.exists() and p.is_file()
    ])
    if on_windows():
        pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)


def is_kanji(char):
    return '\u4e00' <= char <= '\u9faf'


def kana(kanji):
    kana = kks.convert(kanji)[0]['hira']
    return kana


def near_last_capture(x, y):
    global prev_capture, new_capture_threshold
    return (
        x >= prev_capture.x - new_capture_threshold
        and x <= prev_capture.x + new_capture_threshold
        and y >= prev_capture.y - new_capture_threshold
        and y <= prev_capture.y + new_capture_threshold
    )


def next_capture():
    global capture_size, prev_capture
    x, y = pyautogui.position()
    if near_last_capture(x, y):
        return
    prev_capture = XY(x, y)
    region = (
        x - capture_size.x // 2,
        y - capture_size.y // 2,
        x + capture_size.x // 2,
        y + capture_size.y // 2
    )
    screenshot = ImageGrab.grab(region)
    text = pytesseract.image_to_string(screenshot, lang='jpn')
    return text


def get_kanji_words(text):
    return list(filter(
        lambda part: re.match(r'[一-龯]+', part),
        re.split(r'[^一-龯]+', text)
    ))


def substrings(s):
    return [s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)]


def all_words(text):
    return [
        s
        for w in get_kanji_words(text)
        for s in substrings(w)
    ]


def pad(s, n, c):
    return s + c * (n - len(s))


def wrap_indent(s, n, indent='  '):
    if len(s) <= n:
        return s
    return s[:n] + '\n' + wrap_indent(f'{indent}{s[n:].strip()}', n, indent)


def run():
    text = next_capture()
    if text is None:
        return
    words = sorted(
        set(all_words(text)),
        key=lambda w: len(w)
    )
    print()
    for word in words:
        translations = jam.lookup(word)
        for v in translations.entries:
            kanji = FWS.join([k.text for k in v.kanji_forms])
            kana = FWS.join([k.text for k in v.kana_forms])
            glosses = '  '.join([g.text for s in v.senses for g in s.gloss])
            print(
                wrap_indent(
                    pad(kanji, 5, FWS)
                    + FWS + pad(kana, 11, FWS)
                    + FWS + glosses,
                    120,
                    18 * FWS
                )
            )


def main():
    setup_tesseract()
    while True:
        run()
        sleep(0.1)


if __name__ == "__main__":
    main()
