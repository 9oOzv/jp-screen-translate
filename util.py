from dataclasses import dataclass
from textwrap import wrap
import os


def first(iterable):
    return next(iter(iterable), None)


def on_windows():
    return os.name == 'nt'


def all_substrings(s):
    return [
        s[i:j] for i in range(len(s))
        for j in range(i + 1, len(s) + 1)
    ]


def clear():
    os.system('cls' if on_windows() else 'clear')


def strings(v):
    return (str(k) for k in v)


def make_column(text, width, whitespace=' ', num_lines=0):
    lines = wrap(text, width)
    lines.extend([''] * max(num_lines - len(lines), 0))
    return '\n'.join(
        (
            line
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
