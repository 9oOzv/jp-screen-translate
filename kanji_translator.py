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
        self.jam = Jamdict()

    @staticmethod
    def only_kanji_kana(text: str) -> str:
        return re.sub(r'[^一-龯ぁ-んァ-ン]', '', text)

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

    @staticmethod
    def find_kanji_sequences(text: str) -> Iterable[str]:
        splits = [
            s
            for part in re.split(r'[^一-龯]{2,}', text)
            if re.search(r'[一-龯]', part)
            for s in all_substrings(part, 6)
        ]
        log.debug({
            'message': 'Kanji splits',
            'text': text,
            'splits': splits,
        })
        return splits

    def kanji_info(self, kanji: str) -> KanjiInfos:
        entries = self.jam.lookup(kanji).entries or []
        return (
            self._jdm_entry_to_dict(entry)
            for entry in entries
        )

    def text_kanji_info(self, text):
        kanji_sequences = sorted(
            self.find_kanji_sequences(text),
            key=len,
            reverse=True
        )
        return (
            info
            for kanji in kanji_sequences
            for info in self.kanji_info(kanji)
        )
