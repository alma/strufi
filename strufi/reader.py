from collections import deque
from collections.abc import Collection, Iterable

from .exceptions import LoadError, _ContinueLoading


class Reader:
    "Helper class to iterate on input data"

    def __init__(self, input_data: str):
        self._data = deque(input_data)
        self.line = 1
        self.column = 0

    def __bool__(self) -> bool:
        return bool(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterable[str]:
        return iter(self._data)

    def get(self) -> str:
        "Peek next character on input (empty string if input is empty)"
        if not self._data:
            return ""
        return self._data[0]

    def pop(self) -> str:
        "Get and pop next character from input (empty string if input is empty)"
        if not self._data:
            return ""
        char = self._data.popleft()
        if char == "\n":
            self.line += 1
            self.column = 0
        else:
            self.column += 1
        return char

    def check(self, chars: Collection[str]) -> str:
        "Get and pop next character from input if it matches expected characters, empty string otherwise"
        if self.get() not in chars:
            return ""
        return self.pop()

    def load_error(
        self,
        message: str = "",
        *,
        actual: str | None = None,
    ) -> LoadError:
        "Raise a LoadError from current location on input"
        msg_parts = ["unexpected "]

        if actual is None:
            actual = self.get()
        if actual:
            msg_parts.append(f"character {actual!r}")
        else:
            msg_parts.append("end of input")

        msg_parts.append(f" at line {self.line} colum {self.column}")

        if message:
            msg_parts.extend([", ", message])

        return LoadError("".join(msg_parts), self.line, self.column)

    def expect(self, chars: Collection[str], error_message: str | None = None) -> str:
        "Get and pop next character from input if it matches expected characters, raise LoadError otherwise"
        result = self.check(chars)
        if not result:
            if error_message is None:
                if isinstance(chars, str) and len(chars) == 1:
                    chars_repr = repr(chars)
                else:
                    chars_repr = f"one of {', '.join(map(repr, sorted(chars)))}"
                error_message = f"expected {chars_repr}"
            raise self.load_error(error_message)
        return result

    def validate(self, chars: Collection[str]) -> str:
        """Get and pop next character from input if it matches expected characters,
        raise _ContinueLoading otherwise"""
        result = self.check(chars)
        if not result:
            raise _ContinueLoading
        return result
