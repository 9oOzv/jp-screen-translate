from PIL import (
    Image,
    ImageFilter
)
from typing import Iterable, TypeAlias
from util import scale_image
from logging import getLogger

log = getLogger('app')

Region: TypeAlias = tuple[int, int, int, int]


class FractionalPartition:

    def __init__(
        self,
        x0,
        y0,
        x1,
        y1
    ):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def pixels(self, width: int, height: int) -> Region:
        return (
            int(self.x0 * width),
            int(self.y0 * height),
            int(self.x1 * width),
            int(self.y1 * height),
        )


class CaptureSet:

    region: Region = None
    scales = [1.0, 0.5, 0.25]
    parts: Iterable[FractionalPartition] = [
        FractionalPartition(0.0, 0.0, 1.0, 1.0),
    ]
    preview_size = 96
    _divs = None

    def __init__(
        self,
        image: Image,
        region=region,
        scales=scales,
        parts: Iterable[FractionalPartition] | None = None,
        auto_parts=None,
        preview_size=preview_size
    ):
        log.debug({
            'message': 'CaptureSet init',
            'region': region,
            'scales': scales,
            'parts': parts,
            'auto_parts': auto_parts,
            'preview_size': preview_size,
        })
        self.original = image
        self.region = region
        self.scales = scales
        self.parts = (
            parts
            if parts
            else self._auto_parts(*auto_parts)
            if auto_parts
            else CaptureSet.parts
        )

    @staticmethod
    def _auto_parts(
        divs_x: int,
        divs_y: int
    ) -> Iterable[FractionalPartition]:
        step_x = 1 / (divs_x + 1)
        step_y = 1 / (divs_y + 1)
        return [
            FractionalPartition(
                i * step_x,
                j * step_y,
                (i + 2) * step_x,
                (j + 2) * step_y,
            )
            for i in range(divs_x)
            for j in range(divs_y)
        ]

    def preview(self):
        _divs = [
            scale_image(
                div,
                max_dimension=self.preview_size
            )
            for div in self.divs()
        ]
        log.debug({
            'message': 'CaptureSet preview',
            'preview_size': self.preview_size,
            'image_sizes': [
                img.size
                for img in _divs
            ]
        })
        return _divs

    def divs(self):
        log.trace({
            'message': 'CaptureSet divs',
            'parts': [
                p.pixels(*self.original.size)
                for p in self.parts
            ],
            'original_size': self.original.size,
        })
        image = self.sharpen(self.original)
        if self._divs:
            return self._divs
        if not self.parts:
            self._divs = [image]
            return self._divs
        else:
            self._divs = [
                image,
                *(
                    image.crop(
                        part.pixels(*image.size)
                    )
                    for part in self.parts
                )
            ]
            return self._divs

    def images(self):
        log.debug({
            'message': 'CaptureSet images',
            'num_divs': len(self.divs()),
            'scales': self.scales,
        })
        return [
            scale_image(div, scale=scale)
            for div in self.divs()
            for scale in self.scales
        ]
