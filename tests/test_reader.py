import pytest

from strufi.exceptions import LoadError, _ContinueLoading
from strufi.reader import Reader


def test_reader():
    reader = Reader("bar\nz ")

    assert reader.get() == "b"
    assert reader
    assert len(reader) == 6
    assert list(reader) == list("bar\nz ")
    assert (reader.line, reader.column) == (1, 0)

    assert reader.pop() == "b"
    assert reader.get() == "a"
    assert reader
    assert len(reader) == 5
    assert list(reader) == list("ar\nz ")
    assert (reader.line, reader.column) == (1, 1)

    assert reader.pop() == "a"
    assert reader.get() == "r"
    assert reader
    assert len(reader) == 4
    assert list(reader) == list("r\nz ")
    assert (reader.line, reader.column) == (1, 2)

    assert reader.pop() == "r"
    assert reader.get() == "\n"
    assert reader
    assert len(reader) == 3
    assert list(reader) == list("\nz ")
    assert (reader.line, reader.column) == (1, 3)

    assert reader.pop() == "\n"
    assert reader.get() == "z"
    assert reader
    assert len(reader) == 2
    assert list(reader) == list("z ")
    assert (reader.line, reader.column) == (2, 0)

    assert reader.pop() == "z"
    assert reader.get() == " "
    assert reader
    assert len(reader) == 1
    assert list(reader) == [" "]
    assert (reader.line, reader.column) == (2, 1)

    assert reader.pop() == " "
    assert reader.get() == ""
    assert not reader
    assert len(reader) == 0
    assert list(reader) == []
    assert (reader.line, reader.column) == (2, 2)

    assert reader.pop() == ""
    assert reader.get() == ""
    assert not reader
    assert len(reader) == 0
    assert list(reader) == []
    assert (reader.line, reader.column) == (2, 2)


def test_reader_check():
    reader = Reader("bar ")

    assert reader.check("b") == "b"
    assert list(reader) == list("ar ")

    assert reader.check("Aa") == "a"
    assert list(reader) == list("r ")

    assert reader.check("z") == ""
    assert list(reader) == list("r ")


def test_reader_load_error():
    reader = Reader("foo\nbar")

    assert [reader.pop() for _ in range(5)] == list("foo\nb")
    assert reader.get() == "a"
    assert (reader.line, reader.column) == (2, 1)

    e = reader.load_error()
    assert isinstance(e, LoadError)
    assert str(e) == "unexpected character 'a' at line 2 colum 1"
    assert e.args == (e.message, e.line, e.column) == (str(e), 2, 1)

    e = reader.load_error("expected 'b'")
    assert str(e) == "unexpected character 'a' at line 2 colum 1, expected 'b'"

    # Override actual character

    e = reader.load_error("expected 'b'", actual="c")
    assert str(e) == "unexpected character 'c' at line 2 colum 1, expected 'b'"

    e = reader.load_error("expected 'b'", actual="")
    assert str(e) == "unexpected end of input at line 2 colum 1, expected 'b'"

    # End of input

    assert [reader.pop() for _ in range(2)] == list("ar")
    assert reader.get() == ""
    assert (reader.line, reader.column) == (2, 3)

    e = reader.load_error("expected '!'")
    assert str(e) == "unexpected end of input at line 2 colum 3, expected '!'"


def test_reader_expect():
    reader = Reader("bar ")

    assert reader.expect("b") == "b"
    assert list(reader) == list("ar ")

    assert reader.expect("Aa") == "a"
    assert list(reader) == list("r ")

    with pytest.raises(LoadError) as e:
        reader.expect("z")
    assert str(e.value) == "unexpected character 'r' at line 1 colum 2, expected 'z'"

    with pytest.raises(LoadError) as e:
        reader.expect("zyx")
    assert str(e.value) == "unexpected character 'r' at line 1 colum 2, expected one of 'x', 'y', 'z'"

    assert list(reader) == list("r ")

    # Custom error message

    with pytest.raises(LoadError) as e:
        reader.expect("zyx", error_message="should be x, y or z")
    assert str(e.value) == "unexpected character 'r' at line 1 colum 2, should be x, y or z"


def test_reader_validate():
    reader = Reader("bar ")

    assert reader.validate("b") == "b"
    assert list(reader) == list("ar ")

    assert reader.validate("Aa") == "a"
    assert list(reader) == list("r ")

    with pytest.raises(_ContinueLoading):
        reader.validate("z")

    assert list(reader) == list("r ")
