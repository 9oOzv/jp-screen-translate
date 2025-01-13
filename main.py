from app import App
from controller import Controller
from app_config import AppConfig
from fire import Fire
from functools import wraps
from hotkeys import hotkeys
import asyncio
from profiler import Profiler


class Main:

    @staticmethod
    @wraps(AppConfig.create)
    def run(**kwargs):
        config = AppConfig.create(**kwargs)
        app = App(config)
        controller = Controller(app)
        with hotkeys(controller):
            asyncio.run(app.start())

    @staticmethod
    @wraps(AppConfig.create)
    def gui(**kwargs):
        args = {
            **kwargs,
            'gui': True
        }
        Main.run(**args)

    @staticmethod
    @wraps(AppConfig.create)
    def cli(**kwargs):
        args = {
            **kwargs,
            'gui': False
        }
        Main.run(**args)

    @staticmethod
    @wraps(AppConfig.create)
    def profile(**kwargs):
        profiler = Profiler(
            file=kwargs.get('profile_file')
        )
        profiler.profile(
            lambda: Main.run(**kwargs)
        )


if __name__ == '__main__':
    Fire(Main)
