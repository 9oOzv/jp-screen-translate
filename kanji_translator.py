import jamdict
import re
from util import (
    all_substrings,
    strings,
)


class KanjiTranslator:

    def __init__(self):
        self.jam = jamdict.Jamdict()

    @staticmethod
    def only_kanji_kana(text):
        return re.sub(r'[^一-龯ぁ-んァ-ン]', '', text)

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

