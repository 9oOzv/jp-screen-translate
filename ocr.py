from PIL import Image
import asyncio
from concurrent.futures import ThreadPoolExecutor


class OCR:

    async def ocr(self, image: Image) -> list[str]:
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                executor,
                self._ocr,
                image
            )
            return text

    def _ocr(self, image: Image) -> list[str]:
        return [
            "This is",
            "a dummy",
            "ocr result;",
        ]
