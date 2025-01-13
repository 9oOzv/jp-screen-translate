from ocr import OCR
from util import on_windows, first
from pyutils8ccr.log import log
from PIL import Image
from pathlib import Path
import os
from typing import Iterator

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


class TesseractOCR(OCR):

    def __init__(self):
        import pytesseract
        self.pytesseract = pytesseract
        tesseract_exe = first([
            p for p in TESSERACT_SEARCH_PATHS
            if p.exists() and p.is_file()
        ])
        if on_windows():
            self.pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)

    def _ocr(self, image: Image) -> list[str]:
        log.debug({
            'message': 'Running Tesseract',
            'img.size': image.size,
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
                image,
                lang='jpn',
                config=f'--psm {psm}'
            )
            for psm in [5, 6]
        ]
