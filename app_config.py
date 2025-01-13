from config import (
    Config,
    Default
)
from util import (
    Color,
    cached_read
)


class AppConfig(Config):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def create(
        *,
        capture_size_x: int = Default(160),
        capture_size_y: int = Default(100),
        capture_offset_x: int = Default(0),
        capture_offset_y: int = Default(-16),
        capture_threshold: int = Default(16),
        interval: float = Default(0.5),
        force_interval: float = Default(10),
        gui: bool = Default(False),
        clear_tty: bool = Default(False),
        max_entries: int = Default(8),
        gui_colors: list[Color] = Default(
            [
                Color.random_hsluv(lum=75, sat=100)
                for _ in range(8)
            ]
        ),
        debug: bool = Default(False),
        profile_file: bool | str = Default(False),
        capture_preview: bool | None = Default(True),
        scales: int | None = Default(1),
        divs: int | None = Default(0),
        kanji_column: int = Default(4),
        kana_column: int = Default(6),
        gloss_column: int = Default(60),
        capture_column: int = Default(36),
        font_size: float = Default(11),
        backends: str = Default('easyocr'),
        openai_api_key: str = Default(None),
        openai_api_key_file: str = Default(None),
        fps: int = Default(24),
        cli_update_interval: float = Default(0.5),
        auto_capture: bool = Default(False),
    ):
        """
        Capture and translate kanji from the screen.

        Args:
            capture_size_x (int): The width of the capture region.
            capture_size_y (int): The height of the capture region.
            capture_threshold (int): The maximum distance from the last capture
                position to trigger a new capture.
            interval (float): The time in seconds to wait between captures.
            force_interval (float): The time in seconds to wait before forcing
                a new capture.
            gui (bool): Whether to show a tooltip with the translation.
            clear_tty (bool): Whether to clear terminal between prints.
            max_entries (int): The maximum number of entries to show in the
                tooltip.
            gui_colors (list[str]): The colors to use for the tooltip entries.
            debug (bool): Whether to log debug messages.
            profile_file (str): The file name to save the profile stats.
            capture_preview (bool): Whether to show a preview of the capture in
                the tooltip.
            backends (str): Comma-separated list of OCR backends to use. The
                possible values are 'tesseract', 'easyocr', and 'openai'.
            scales (int): Number of scaled versions of the capture to use for
                OCR.
            divs (int): Divide capture region to multiplw parts for OCR.
            kanji_column (int): The width of the kanji column in the tooltip.
            kana_column (int): The width of the kana column in the tooltip.
            gloss_column (int): The width of the gloss column in the tooltip.
            capture_column (int): The width of the capture column in the
                tooltip.
            font_size (float): The font size to use in the tooltip.
            fps (int): The frames per second to use for the tooltip.
            cli_update_interval (float): The time in seconds to wait between
            auto_capture (bool): Whether to automatically capture and translate according to the configured intervals/thresholds.
        """
        args = {
            k: v
            for k, v in locals().items()
            if k != 'self'
        }
        return AppConfig(**args)

    @property
    def openai_api_key(self):
        key = self._get('openai_api_key')
        key_file = self._get('openai_api_key_file')
        return (
            key
            if key is not None
            else cached_read(key_file, 'r').strip()
            if key_file is not None
            else None
        )

    @property
    def log_level(self) -> str:
        if self._get('debug'):
            return 'DEBUG'
        return 'INFO'

    @property
    def backends(self) -> list[str]:
        return [
            b.strip()
            for b
            in self._get('backends').split(',')
        ]

