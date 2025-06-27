class LoadError(ValueError):
    "Exception raised when input data is not parsable"

    def __init__(self, message: str, line: int | None = None, column: int | None = None):
        super().__init__(message, line, column)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return self.message


class _ContinueLoading(Exception):
    "Temporary exception used to exit from a parsing function"


class DumpError(ValueError):
    "Exception raised when data is not serializable"
