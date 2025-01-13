from ocr import OCR
import base64
from PIL import Image
from io import BytesIO
from textwrap import dedent
from pyutils8ccr.log import log

openai = None
Completion = None


system_prmopt = dedent("""
    Transcribe any japanese text in the given image. Answer with only the
    transcribed text and nothing else. If the image has multiple pieces of
    text. Separate the pieces with a newline character. If the text has
    multiple lines, Separate the lines of text with a newline character
    a newline character.
""")


system_message = {
    "role": "system",
    "content": [
        {
            "type": "text",
            "text": system_prmopt,
        },
    ],
}


def image_message(image_b64: str):
    return {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"
                },
            },
        ]
    }


def encode_image(image: Image) -> str:
    with BytesIO() as output:
        image.save(output, format="PNG")
        bytes = output.getvalue()
        return base64.b64encode(bytes).decode("utf-8")


class OpenAIOCR(OCR):

    def __init__(self, api_key: str = None):
        global OpenAI, Completion
        import openai
        OpenAI = openai.OpenAI
        Completion = openai.types.Completion
        if api_key is not None:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = OpenAI()

    def completion(self, image_b64: str) -> Completion:
        messages = [
            system_message,
            image_message(image_b64)
        ]
        log.debug({
            'messages': messages
        })
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

    def _ocr(self, image: Image) -> str:
        image_b64 = encode_image(image)
        completion = self.completion(image_b64)
        text = completion.choices[0].message.content
        return text.split("\n")
