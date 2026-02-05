"""Small, composable pipeline utilities.

This module exposes two pipeline styles:

- ``Pipe`` for single-value transformations.
- ``PipeStream`` for stream-style processing where stages can fan out.

Use ``spread(...)`` when a stage returns an iterable and you want each element
processed as its own stream item.
"""

from collections.abc import Iterable
from typing import Any, Callable, Iterator, List

__all__ = ["Pipe", "PipeStream", "spread", "keep", "tap"]

_NON_STREAM_TYPES = (str, bytes)


class Spread:
    """Internal marker used to represent fan-out in ``PipeStream``."""

    def __init__(self, values: Iterable[Any]) -> None:
        self._values = values

    def __iter__(self) -> Iterator[Any]:
        return iter(self._values)


Stage = Callable[[Any], Any]


def spread(func: Stage) -> Stage:
    """Wrap ``func`` so iterable results are emitted item-by-item.

    ``PipeStream`` treats ``spread(func)`` as fan-out.
    ``Pipe`` collapses the marker to ``list(...)`` to preserve single-value flow.
    """

    def _spread_after(value: Any) -> Any:
        result = func(value)
        if isinstance(result, Iterable) and not isinstance(result, _NON_STREAM_TYPES):
            return Spread(result)
        return result

    _spread_after.__name__ = "spread({})".format(getattr(func, "__name__", repr(func)))
    return _spread_after


def _emit(value: Any) -> Iterator[Any]:
    if isinstance(value, Spread):
        yield from value
    else:
        yield value


class Pipe:
    """Single-value pipeline.

    Example:
        >>> p = Pipe("hello") >> str.upper >> (lambda s: s[::-1])
        >>> p()
        'OLLEH'
    """

    def __init__(self, input_data: Any = None) -> None:
        self.stack = []  # type: List[Stage]
        self.input_data = input_data

    def __rshift__(self, stage: Stage) -> "Pipe":
        self.stack.append(stage)
        return self

    def __call__(self, input_data: Any = None) -> Any:
        data = self.input_data if input_data is None else input_data
        for stage in self.stack:
            data = stage(data)
            if isinstance(data, Spread):
                data = list(data)
        return data

    def __repr__(self) -> str:
        names = " >> ".join(getattr(stage, "__name__", repr(stage)) for stage in self.stack)
        return "Pipe({})".format(names)


class PipeStream:
    """Stream pipeline with explicit fan-out via ``spread(...)``.

    If the initial input is an iterable (except ``str``/``bytes``), items are
    emitted as the initial stream.
    """

    def __init__(self, input_data: Any = None) -> None:
        self.stack = []  # type: List[Stage]
        if input_data is not None and isinstance(input_data, Iterable) and not isinstance(input_data, _NON_STREAM_TYPES):
            self.input_data = Spread(input_data)
        else:
            self.input_data = input_data

    def __rshift__(self, stage: Stage) -> "PipeStream":
        self.stack.append(stage)
        return self

    def __call__(self, input_data: Any = None) -> Iterator[Any]:
        data = self.input_data if input_data is None else input_data
        if data is None:
            return iter(())
        if isinstance(data, Iterable) and not isinstance(data, _NON_STREAM_TYPES) and not isinstance(data, Spread):
            data = Spread(data)

        stream = list(_emit(data))
        for stage in self.stack:
            next_stream = []
            for item in stream:
                for emitted in _emit(stage(item)):
                    next_stream.append(emitted)
            stream = next_stream
        return iter(stream)

    def __iter__(self) -> Iterator[Any]:
        return self()

    @classmethod
    def from_pipe(cls, pipe: Pipe, input_data: Any = None) -> "PipeStream":
        """Create a ``PipeStream`` from an existing ``Pipe`` stage stack."""

        stream = cls(input_data)
        stream.stack = list(pipe.stack)
        return stream

    def __repr__(self) -> str:
        names = " >> ".join(getattr(stage, "__name__", repr(stage)) for stage in self.stack)
        return "PipeStream({})".format(names)


def keep(predicate: Callable[[Any], bool]) -> Stage:
    """Return a stage that keeps only values where ``predicate(value)`` is true."""

    def _keep(value: Any) -> Spread:
        if predicate(value):
            return Spread((value,))
        return Spread(())

    return _keep


def tap(func: Callable[[Any], None]) -> Stage:
    """Return a stage that performs a side effect and passes through values."""

    def _tap(value: Any) -> Any:
        func(value)
        return value

    return _tap
