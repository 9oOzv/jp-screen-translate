from kanji_translator import KanjiInfo
from itertools import islice
from util import (
    make_column,
    combine_columns
)
from textwrap import fill
from pyutils8ccr.log import log

FWS = '　'


class CliFormatter():

    def __init__(
        self,
        max_entries: int = 10,
        kanji_col_width: int = 4,
        kana_col_width: int = 6,
        gloss_col_width: int = 60,
    ):
        self.max_entries = max_entries
        self.kanji_col_width = kanji_col_width
        self.kana_col_width = kana_col_width
        self.gloss_col_width = gloss_col_width
        self.text = ''

    def format(
        self,
        capture: str,
        infos: list[KanjiInfo],
        max_entries: int = 10
    ):
        log.debug({'capture': capture, 'infos': infos})
        lines = []
        # limit generator output to max_entries
        for info in islice(infos, self.max_entries):
            kanji = FWS.join(info['kanji'])
            kana = FWS.join(info['kana'])
            gloss = '  '.join(info['gloss'])
            tmp_columns = [
                make_column(kanji, self.kanji_col_width),
                make_column(kana, self.kana_col_width),
                make_column(gloss, self.gloss_col_width)
            ]
            num_lines = max(
                c.count('\n') + 1
                for c in tmp_columns
            )
            line = combine_columns(
                make_column(
                    kanji,
                    self.kanji_col_width,
                    whitespace=FWS,
                    num_lines=num_lines
                ),
                make_column(
                    kana,
                    self.kana_col_width,
                    whitespace=FWS,
                    num_lines=num_lines
                ),
                make_column(
                    gloss,
                    self.gloss_col_width,
                    num_lines=num_lines
                ),
                separator='    '
            )
            lines.append(line)
        wrapped_capture = fill(
            capture,
            width=(
                self.kanji_col_width
                + self.kana_col_width
                + self.gloss_col_width
            ),
            break_long_words=True
        )
        self.text = '\n'.join(
            [
                wrapped_capture,
                *lines
            ]
        )
        log.debug({'text': self.text})
