from jamdict import Jamdict
from jamdict.jmdict import JMDEntry
import re
from util import (
    all_substrings,
    strings
)
from logging import getLogger
from typing import (
    Iterable,
    TypeAlias
)


log = getLogger('app')

KanjiInfos: TypeAlias = Iterable[dict[str, list[str]]]


class KanjiTranslator:

    def __init__(self):
        self.jam = Jamdict(memory_mode=True)

    _sane_kanji_seq_re = re.compile(r'^([一-龯]+[ぁ-んァ-ン]?)+[ぁ-んァ-ン]?$')

    @staticmethod
    def sane_kanji_seq(text: str) -> bool:
        return bool(
            KanjiTranslator._sane_kanji_seq_re.match(
                text
            )
        )

    @staticmethod
    def _jdm_entry_to_dict(
        entry: JMDEntry
    ) -> dict[str, list[str]]:
        return {
            'kanji': strings(entry.kanji_forms),
            'kana': strings(entry.kana_forms),
            'gloss': [
                g for sense in entry.senses
                for g in strings(sense.gloss)
            ]
        }

    _non_kanji_kana_re = re.compile(r'[^一-龯ぁ-んァ-ン]+')

    @staticmethod
    def jpn_sequences(text: str) -> str:
        return re.split(
            KanjiTranslator._non_kanji_kana_re,
            text
        )

    def kanji_info(self, kanji: str) -> KanjiInfos:
        entries = self.jam.lookup(kanji).entries or []
        return [
            self._jdm_entry_to_dict(entry)
            for entry in entries
        ]

    @staticmethod
    def kanji_count(word: str) -> int:
        return len(
            [
                c
                for c in word
                if '一' <= c <= '龯'
            ]
        )

    @staticmethod
    def info_sort_key(info: dict) -> int:
        num_kanji = max(
            KanjiTranslator.kanji_count(k)
            for k in info['kanji']
        )
        num_chars = max(
            len(k)
            for k in info['kanji']
        )
        return (num_kanji, num_chars)


    def text_kanji_info(self, text):
        log.debug({'text': text})
        jpn_seqs = self.jpn_sequences(text)
        seqs = set([
            seq
            for jpn_seq in jpn_seqs
            for seq in all_substrings(jpn_seq, 5)
        ])
        kanji_seqs = [s for s in seqs if self.sane_kanji_seq(s)]
        log.trace({'kanji_seqs': kanji_seqs})
        infos = [
            info
            for kanji in kanji_seqs
            for info in self.kanji_info(kanji)
        ]
        sorted_infos = sorted(
            infos,
            key=self.info_sort_key,
            reverse=True
        )
        log.trace({'sorted_infos': sorted_infos})
        return sorted_infos
