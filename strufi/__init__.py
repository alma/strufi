"""
Library to load HTTP structure field values
according to RFC9651 <https://www.rfc-editor.org/rfc/rfc9651.html>
"""

from collections.abc import Callable, Iterable

from . import dump_primitives, load_primitives
from .exceptions import DumpError, LoadError, _ContinueLoading
from .reader import Reader
from .types import Item, ItemList


def _wrap_load[T](load_func: Callable[[Reader], T], data: str, strict: bool) -> T:
    try:
        data = data.encode("utf-8").decode("ascii")
    except ValueError as e:
        raise LoadError(str(e)) from e

    reader = Reader(data)
    load_primitives.discard_whitespaces(reader)

    try:
        result = load_func(reader)
    except _ContinueLoading:
        raise reader.load_error()

    if strict:
        load_primitives.discard_whitespaces(reader)
        if reader:
            raise reader.load_error("expected end of input")

    return result


def load_item(data: str, strict: bool = True) -> Item:
    "Load data as an HTTP structured item, raise LoadError in case of invalid input"
    return _wrap_load(load_primitives.load_item, data, strict)


def load_list(data: str, strict: bool = True) -> list[Item | ItemList]:
    "Load data as an HTTP structured list, raise LoadError in case of invalid input"
    return _wrap_load(load_primitives.load_list, data, strict)


def load_dict(data: str, strict: bool = True) -> dict[str, Item | ItemList]:
    "Load data as an HTTP structured dictionnary, raise LoadError in case of invalid input"
    return _wrap_load(load_primitives.load_dict, data, strict)


def _wrap_dump[T](dump_func: Callable[[T], Iterable[str]], item: T) -> str:
    return "".join(dump_func(item))


def dump_item(item: Item | ItemList) -> str:
    "Dump a value item as an HTTP structured item, raise DumpError in case of invalid value"
    return _wrap_dump(dump_primitives.dump_item_or_inner_list, item)


def dump_list(item: list[Item | ItemList]) -> str:
    "Dump a list as an HTTP structured list, raise DumpError in case of invalid value"
    return _wrap_dump(dump_primitives.dump_list, item)


def dump_dict(item: dict[str, Item | ItemList]) -> str:
    "Dump a dict as an HTTP structured dictionnary, raise DumpError in case of invalid value"
    return _wrap_dump(dump_primitives.dump_dict, item)


__all__ = [
    "DumpError",
    "LoadError",
    "dump_dict",
    "dump_item",
    "dump_list",
    "load_dict",
    "load_item",
    "load_list",
]
