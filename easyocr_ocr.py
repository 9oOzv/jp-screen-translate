from ocr import OCR
from pyutils8ccr.log import log
from PIL import Image
from typing import Iterator
import numpy


class EasyOCR(OCR):

    def __init__(self):
        from easyocr import Reader
        self.easyocr_reader = Reader(['ja'])

    def _ocr(self, image: Image) -> Iterator[str]:
        log.debug({
            'message': 'Running EasyOCR',
            'img.size': image.size,
        })
        if not self.easyocr_reader:
            from easyocr import Reader
            self.easyocr_reader = Reader(['ja'])
        texts = [
            v[1]
            for v in
            self.easyocr_reader.readtext(numpy.array(image))
        ]
        return texts
