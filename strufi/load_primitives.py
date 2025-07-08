import base64
import string
from datetime import UTC, datetime

from .exceptions import _ContinueLoading
from .reader import Reader
from .types import BareItem, Item, ItemList, Parameters


def discard_whitespaces(reader: Reader) -> None:
    while reader.get().isspace():
        reader.pop()


def load_digits(reader: Reader) -> str:
    digits = []
    while reader.get().isdigit():
        digits.append(reader.pop())

    if digits:
        return "".join(digits)
    else:
        raise _ContinueLoading


def load_number(reader: Reader) -> int | float:
    if reader.check("-"):
        sign = -1
    else:
        sign = 1

    try:
        digits = load_digits(reader)
    except _ContinueLoading:
        if sign == -1:
            raise reader.load_error("expected a digit")
        else:
            raise

    if reader.check("."):
        try:
            dec_digits = load_digits(reader)
        except _ContinueLoading:
            raise reader.load_error("expected a digit")

        return sign * float(f"{digits}.{dec_digits}")
    else:
        return sign * int(digits)


STRING_CHARS = frozenset(chr(i) for i in range(0x20, 0x7E + 1))


def load_string(reader: Reader) -> str:
    reader.validate('"')

    content: list[str] = []

    while reader:
        match reader.pop():
            case '"':
                return "".join(content)
            case "\\":
                content.append(reader.expect({'"', "\\"}))
            case char if char in STRING_CHARS:
                content.append(char)
            case char:
                raise reader.load_error("character is not allowed in string", actual=char)

    raise reader.load_error("expected '\"'")


TOKEN_START_CHARS = frozenset(string.ascii_letters) | {"*"}
TOKEN_CHARS = frozenset("!#$%&'*+-.^_`|~:/") | set(string.digits) | set(string.ascii_letters)


def load_token(reader: Reader) -> str:
    content = [reader.validate(TOKEN_START_CHARS)]

    # should also allow unicode characters according to RFC9110
    # but this is not useful for now
    while char := reader.check(TOKEN_CHARS):
        content.append(char)

    return "".join(content)


BYTES_CHARS = frozenset(string.ascii_letters) | set(string.digits) | set("+/=")


def load_bytes(reader: Reader) -> bytes:
    reader.validate(":")
    content: list[str] = []

    while reader:
        match reader.pop():
            case ":":
                try:
                    return base64.b64decode("".join(content))
                except ValueError as e:
                    raise reader.load_error(f"invalid base64 string: {e}", actual=":") from e
            case char if char in BYTES_CHARS:
                content.append(char)
            case char:
                raise reader.load_error("character is not allowed in base64 string", actual=char)

    raise reader.load_error("expected ':'")


BOOLEAN_CHARS = frozenset("01")


def load_boolean(reader: Reader) -> bool:
    reader.validate("?")
    return reader.expect(BOOLEAN_CHARS) == "1"


def load_date(reader: Reader) -> datetime:
    reader.validate("@")

    try:
        value = load_number(reader)
    except _ContinueLoading:
        raise reader.load_error("expected a digit")

    if isinstance(value, float):
        raise reader.load_error("decimal number is not accepted as a date", actual=".")

    return datetime.fromtimestamp(value, UTC)


def load_display_string(reader: Reader) -> str:
    reader.validate("%")
    reader.expect('"')
    content = bytearray()

    while reader:
        match reader.pop():
            case '"':
                try:
                    return content.decode("utf-8")
                except ValueError as e:
                    raise reader.load_error(f"cannot decode string: {e}", actual='"') from e
            case "%":
                content.append(
                    int(
                        reader.expect(string.hexdigits, error_message="expected an hexadecimal digit")
                        + reader.expect(string.hexdigits, error_message="expected an hexadecimal digit"),
                        16,
                    )
                )
            case char if char in STRING_CHARS:
                content.extend(char.encode("utf-8"))
            case char:
                raise reader.load_error("character is not allowed in display string", actual=char)

    raise reader.load_error("expected '\"'")


ITEM_LOAD_FUNCTIONS = [
    load_number,
    load_string,
    load_token,
    load_bytes,
    load_boolean,
    load_date,
    load_display_string,
]


def load_bare_item(reader: Reader) -> BareItem:
    for load_func in ITEM_LOAD_FUNCTIONS:
        try:
            return load_func(reader)
        except _ContinueLoading:
            pass

    raise _ContinueLoading


KEY_START_CHARS = frozenset(string.ascii_lowercase) | {"*"}
KEY_CHARS = KEY_START_CHARS | set(string.digits) | {"_", "-", "."}


def load_key(reader: Reader) -> str:
    key = [reader.validate(KEY_START_CHARS)]

    while char := reader.check(KEY_CHARS):
        key.append(char)

    return "".join(key)


def load_parameters(reader: Reader) -> Parameters:
    parameters = {}

    while reader:
        if not reader.check(";"):
            break

        discard_whitespaces(reader)

        try:
            key = load_key(reader)
        except _ContinueLoading:
            raise reader.load_error("expected a key")

        if reader.check("="):
            try:
                value = load_bare_item(reader)
            except _ContinueLoading:
                raise reader.load_error("expected a value")
            parameters[key] = value
        else:
            parameters[key] = True

    return parameters


def load_item(reader: Reader) -> Item:
    return (load_bare_item(reader), load_parameters(reader))


def load_inner_list(reader: Reader) -> ItemList:
    reader.validate("(")

    values: list[Item] = []

    while reader:
        discard_whitespaces(reader)

        if reader.check(")"):
            return values, load_parameters(reader)

        try:
            val = load_item(reader)
        except _ContinueLoading:
            raise reader.load_error("expected an item")

        if reader.get() != ")" and not reader.get().isspace():
            raise reader.load_error("expected ')' or space")
        values.append(val)

    raise reader.load_error("expected ')'")


def load_item_or_inner_list(reader: Reader) -> Item | ItemList:
    try:
        return load_inner_list(reader)
    except _ContinueLoading:
        return load_item(reader)


def load_list(reader: Reader) -> list[Item | ItemList]:
    values = []

    while reader:
        try:
            values.append(load_item_or_inner_list(reader))
        except _ContinueLoading:
            raise reader.load_error("expected an item")

        discard_whitespaces(reader)

        if not reader.check(","):
            break

        discard_whitespaces(reader)
        if not reader:
            raise reader.load_error("consider removing trailing comma")

    return values


def load_dict(reader: Reader) -> dict[str, Item | ItemList]:
    mapping = {}

    while reader:
        try:
            key = load_key(reader)
        except _ContinueLoading:
            raise reader.load_error("expected a key")

        if reader.check("="):
            try:
                mapping[key] = load_item_or_inner_list(reader)
            except _ContinueLoading:
                raise reader.load_error("expected an item")
        else:
            mapping[key] = (True, load_parameters(reader))

        discard_whitespaces(reader)

        if not reader.check(","):
            break

        discard_whitespaces(reader)
        if not reader:
            raise reader.load_error("consider removing trailing comma")

    return mapping
