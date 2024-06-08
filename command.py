from inspect import (
    Parameter,
    Signature,
    signature
)
from logging import getLogger
from fire import Fire


log = getLogger()


def is_vararg(p: Parameter):
    return p.kind in [
        Parameter.VAR_POSITIONAL,
        Parameter.VAR_KEYWORD,
    ]


def is_good(p: Parameter):
    if p.name in ['self', 'cls', 'args', 'kwargs']:
        return False
    if is_vararg(p):
        return True
    return True


def is_default(p: Parameter):
    return p.default != Parameter.empty


def is_pos(p: Parameter):
    if not is_good(p):
        return False
    if p.kind == Parameter.POSITIONAL_ONLY:
        return True
    if p.kind == Parameter.POSITIONAL_OR_KEYWORD and not is_default(p):
        return True
    return False


def is_kw(p: Parameter):
    if not is_good(p):
        return False
    if p.kind == Parameter.KEYWORD_ONLY:
        return True
    if p.kind == Parameter.POSITIONAL_OR_KEYWORD and is_default(p):
        return True
    return False


def force_kw(p: Parameter):
    return Parameter(
        name=p.name,
        kind=Parameter.KEYWORD_ONLY,
        default=p.default,
        annotation=p.annotation,
    )


def force_pos(p: Parameter):
    return Parameter(
        name=p.name,
        kind=Parameter.POSITIONAL_ONLY,
        default=p.default,
        annotation=p.annotation,
    )


class Commands:

    commands = {}

    def create(self, cls, method_name: str):

        def _positionals(params):
            return [force_pos(p) for p in params if is_pos(p)]

        def _keywords(params):
            return [p for p in params if is_kw(p)]

        method = getattr(cls, method_name)
        class_params = signature(cls).parameters.values()
        class_kw_params = _keywords(class_params)
        method_params = signature(method).parameters.values()
        method_kw_params = _keywords(method_params)
        method_pos_params = _positionals(method_params)

        def _filter_kwargs(kwargs, names):
            return {k: v for k, v in kwargs.items() if k in names}

        def _class_kwargs(kwargs):
            return _filter_kwargs(kwargs, [p.name for p in class_kw_params])

        def _method_kwargs(kwargs):
            return _filter_kwargs(kwargs, [p.name for p in method_kw_params])

        def wrapper(*args, **kwargs):
            log.trace({
                'args': args,
                'kwargs': kwargs,
                'class_params': class_params,
                'class_kw_params': class_kw_params,
                'method_params': method_params,
                'method_pos_params': method_pos_params,
                'method_kw_params': method_kw_params,
            })
            assert len(args) >= len(method_pos_params)
            instance = cls(
                **_class_kwargs(kwargs)
            )
            instance_method = getattr(
                instance,
                method_name
            )
            return instance_method(
                *args,
                **_method_kwargs(kwargs)
            )

        wrapper.__name__ = method_name
        wrapper.__signature__ = Signature(
            parameters=[
                *method_pos_params,
                *method_kw_params,
                *class_kw_params,
            ]
        )
        wrapper.__doc__ = f"{method.__doc__}\n{cls.__doc__}"
        self.commands[method_name] = wrapper

    def alias(self, name: str, command: str, **fixed):
        """
        Create an alias for a command with fixed kw arguments.

        Args:
            name (str): The name of the alias.
            command (str): The name of the command to alias.
            fixed (dict): Fixed arguments to pass to the command.
        """
        command = self.commands[command]
        command_params = signature(command).parameters.values()

        def wrapper(*args, **kwargs):
            return command(*args, **{**kwargs, **fixed})
        parameters = [
            p for p in command_params
            if p.name not in fixed
        ]
        wrapper.__name__ = name
        wrapper.__signature__ = Signature(parameters=parameters)
        wrapper.__doc__ = command.__doc__
        self.commands[name] = wrapper

    def fire(self):
        self.commands['help'] = lambda: Fire(commands, command='--help')
        Fire(self.commands)
