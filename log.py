#!/usr/bin/env python3
from logging import (
    getLogger,
    Formatter,
    StreamHandler,
    INFO,
)
import json
import sys
from colorama import (
    Fore,
    Style,
)

TRACE = 5


class JSONFormatter(Formatter):

    def __init__(self, pretty=False, *args, **kwargs):
        self.pretty = pretty
        self.printer = self._pretty if pretty else self._json
        super().__init__(*args, **kwargs)

    def _json(self, message):
        try:
            return json.dumps(message)
        except Exception as e:
            return json.dumps({'error': str(e)})

    def _pretty(self, message):
        level = message['levelno']
        try:
            return '\n'.join([
                (
                    f'{Fore.MAGENTA if level > INFO else Fore.CYAN}{Style.BRIGHT}'
                    f'[{message.get("timestamp", "")}]'
                    f'{message.get("level", "")}:'
                    f'{message.get("message", "")}'
                    f'{Style.RESET_ALL}'
                ),
                *[
                    f'{Style.DIM if level < INFO else ""}'
                    f'{key}: {value}'
                    f'{Style.RESET_ALL}'
                    for key, value in message.items()
                ]
            ])
        except Exception as e:
            return str(e)

    def format(self, record):
        if isinstance(record.msg, dict):
            if 'lazy' in record.msg and callable(record.msg['lazy']):
                record.msg = record.msg['lazy']
        message = {}
        message['timestamp'] = self.formatTime(record, self.datefmt)
        message['level'] = record.levelname
        message['levelno'] = record.levelno
        message['filename'] = record.filename
        message['lineno'] = record.lineno
        message['funcName'] = record.funcName
        if (isinstance(record.msg, dict)):
            message.update(record.msg)
        else:
            message['message'] = record.getMessage()
        record.message = self.printer(message)
        return record.message


def configure_logger(name=None, level=INFO, pretty=False):
    log = getLogger(name) if name else getLogger()
    log.setLevel(level)
    handler = StreamHandler(stream=sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(JSONFormatter(pretty=pretty))
    log.addHandler(handler)

    def trace(msg, *args, **kwargs):
        log._log(TRACE, msg, args, **kwargs)
    log.trace = trace

configure_logger()
