import re
from typing import Any
import os
from pyutils8ccr.log import log


class Default():

    def __init__(self, value: Any):
        self.value = value

    def __repr__(self):
        return repr(self.value)


class Config():

    def __init__(self, **kwargs):
        self.keys = []
        self.calculated = {}
        self.opts = {}
        self.env = {}
        self.defaults = {}
        for key, value in kwargs.items():
            self.keys.append(key)
            if not (
                self._maybe_option(key, value)
                or self._maybe_env(key)
                or self._maybe_default(key, value)
            ):
                raise ValueError(f'No value for {key}')
        log.debug({
            'config': self.__dict__
        })

    def _maybe_option(self, key, value):
        log.debug({
            'key': key,
            'value': value,
        })
        if isinstance(value, Default):
            return False
        self.opts[key] = value
        return True

    def _maybe_env(self, key):
        env_name = re.sub(
            r'[^A-Z0-9]',
            '_',
            key.upper()
        )
        log.debug({
            'key': key,
            'env_name': env_name,
        })
        if env_name not in os.environ:
            return False
        self.env[key] = os.environ[env_name]
        return True

    def _maybe_default(
        self,
        key,
        default,
    ):
        log.debug({
            'key': key,
            'default': default,
        })
        if not isinstance(default, Default):
            return False
        self.defaults[key] = default.value
        return True

    def update(self, **kwargs):
        for key, value in kwargs.items():
            log.debug({
                'key': key,
                'value': value,
            })
            if key not in self.keys:
                raise ValueError(f'No such key: {key}')
            self.opts[key] = value

    def _get(self, key):
        if key not in self.keys:
            raise ValueError(f'No such key: {key}')
        if key in self.opts:
            return self.opts[key]
        if key in self.env:
            return self.env[key]
        if key in self.defaults:
            return self.defaults[key]

    def __getattr__(self, key):
        return self._get(key)
