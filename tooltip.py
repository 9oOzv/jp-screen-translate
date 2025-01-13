import tkinter as tk
from contextlib import contextmanager
from PIL import (
    Image,
    ImageTk
)
from pyutils8ccr.log import log
import pyautogui


class Tooltip(tk.Tk):
    offset_x = 64
    offset_y = 64
    labels = []
    texts = []
    images = []
    frame = None
    image_frame = None
    # Need to keep a reference to the images. Otherwise they will be garbage
    # collected or something.
    photoImages = []
    font_size: float = 12

    def __init__(
        self,
        font_size: float = 12,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.font_size = font_size
        bg = 'black'
        self.overrideredirect(True)
        self.attributes('-alpha', 0.9)
        self.attributes('-topmost', True)
        self.title("Transparent Window")
        self.configure(bg=bg)
        self.frame = tk.Frame(self, bg='black')
        self.frame.pack(anchor='w')
        self.image_frame = tk.Frame(self, bg='red')
        self.image_frame.pack(anchor='w')
        self.update()

    def add(self, text, color='black'):
        log.debug({
            'message': 'Adding text to tooltip',
            'text': text,
        })
        self.texts.append({'text': text, 'color': color})

    def add_image(self, image: Image):
        log.debug({
            'message': 'Adding image to tooltip',
            'size': image.size,
        })
        self.images.append(image)

    def clear(self):
        self.texts = []
        self.images = []
        self.photoImages = []

    def hide(self):
        self.withdraw()

    @contextmanager
    def hidden(self):
        try:
            self.hide()
            yield
        finally:
            self.show()

    def show(self):
        self.deiconify()

    def update(self):
        for label in self.labels:
            label.pack_forget()
            label.destroy()
        self.photoImages = [
            ImageTk.PhotoImage(image)
            for image in self.images
        ]
        for i, image in enumerate(self.photoImages):
            label = tk.Label(self.image_frame, image=image)
            label.grid(row=0, column=i)
            self.labels.append(label)
        for text in self.texts:
            label = tk.Label(
                self.frame,
                text=text['text'],
                font=(
                    "Helvetica",
                    self.font_size,
                ),
                justify='left',
                bg='black',
                fg=text['color']
            )
            label.pack(anchor='w')
            self.labels.append(label)
        self.image_frame.pack_forget()
        self.image_frame.pack(anchor='w')
        self.frame.pack_forget()
        self.frame.pack(anchor='w')
        self.update_position()

    def update_position(self):
        x, y = pyautogui.position()
        x += self.offset_x
        y += self.offset_y
        w = max(
            self.frame.winfo_reqwidth(),
            self.image_frame.winfo_reqwidth()
        )
        h = (
            self.frame.winfo_reqheight()
            + self.image_frame.winfo_reqheight()
        )
        # Make sure the window is not outside the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        if x + w > screen_width:
            x -= w + 2 * self.offset_x
        if y + h > screen_height:
            y -= h + 2 * self.offset_y
        self.geometry(f'{w}x{h}+{x}+{y}')
        super().update()
        super().update_idletasks()

    @property
    def visible(self):
        return self.winfo_ismapped()
