from textwrap import wrap
import os
from random import randint
from hsluv import hsluv_to_rgb
from contextlib import contextmanager
from typing import Iterable
from PIL import Image


def first(iterable):
    return next(iter(iterable), None)


def on_windows():
    return os.name == 'nt'


def all_substrings(s: Iterable, n: int = 6):
    return [
        s[i:j] for i in range(len(s))
        for j in range(i, i + n)
    ]


def clear_tty():
    os.system('cls' if on_windows() else 'clear')


def strings(v):
    return [str(k) for k in v]


def make_column(text, width, whitespace=' ', num_lines=0):
    text = text.replace(whitespace, ' ')
    lines = wrap(text, width, break_long_words=False)
    lines.extend([''] * max(num_lines - len(lines), 0))
    return '\n'.join(
        (
            line
            .strip()
            .ljust(width, whitespace)
            .replace(' ', whitespace)
        )
        for line in lines
    )


def combine_columns(*columns, separator=' '):
    columns = [
        c.splitlines()
        for c in columns
    ]
    return '\n'.join(
        separator.join(line)
        for line in zip(*columns)
    )


@contextmanager
def nothing():
    yield


def sliding_window(s, width):
    for i in range(len(s) - width + 1):
        yield s[i:i + width]


def _insert(a: str, b: str, i: int) -> None:
    return a[:i] + b + a[i+len(b):]


def scale_image(
    img: Image,
    scale: float = None,
    max_dimension: int = None
):
    scale = min(
        (
            scale
            if scale
            else 999999
        ),
        (
            max_dimension / max(img.size)
            if max_dimension
            else 999999
        )
    )
    return img.resize((
        int(img.width * scale),
        int(img.height * scale),
    ))

def adjust_image(img: Image):
    return img.quantize(4).convert('RGB')


class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    @staticmethod
    def from_hsluv(hue, sat, lum):
        return Color(*(int(255 * v) for v in hsluv_to_rgb((hue, sat, lum))))

    def __str__(self):
        return f'#{self.r:02x}{self.g:02x}{self.b:02x}'

    @staticmethod
    def random_hsluv(hue=None, sat=None, lum=None):
        hue = randint(0, 359) if hue is None else hue
        sat = randint(0, 100) if sat is None else sat
        lum = randint(0, 100) if lum is None else lum
        return Color.from_hsluv(hue, sat, lum)
