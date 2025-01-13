from app import App
from typing import Awaitable
from asyncio import run_coroutine_threadsafe
from pyutils8ccr.log import log

class Controller():

    def __init__(self, app: App):
        self.app = app

    def _do(self, f: Awaitable):
        try:
            future = run_coroutine_threadsafe(f, self.app.loop)
            future.result()
        except Exception as e:
            log.error(
                {
                    'message': 'Error',
                    'error': e,
                }
                , exc_info=e
            )

    async def _toggle_tooltip(self):
        tooltip = self.app.tooltip
        if tooltip.visible():
            tooltip.hide()
        else:
            tooltip.show()

    def toggle_tooltip(self):
        self._do(self._toggle_tooltip())

    async def _capture(self):
        app = self.app
        await app.capture()
        await app.translate()
        await app.format()

    def capture(self):
        self._do(self._capture())

    async def _exit(self):
        self.app.exit = True

    def exit(self):
        self._do(self._exit())
