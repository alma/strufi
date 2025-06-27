from datetime import UTC, datetime

import pytest

from strufi.exceptions import LoadError, _ContinueLoading
from strufi.load_primitives import (
    discard_whitespaces,
    load_bare_item,
    load_boolean,
    load_bytes,
    load_date,
    load_dict,
    load_digits,
    load_display_string,
    load_inner_list,
    load_item,
    load_item_or_inner_list,
    load_key,
    load_list,
    load_number,
    load_parameters,
    load_string,
    load_token,
)
from strufi.reader import Reader


def check_load_function(load_func, input_data, expected, remaining_data=""):
    reader = Reader(input_data)
    value = load_func(reader)
    assert value == expected
    assert list(reader) == list(remaining_data)
    return value


def check_load_function_error(load_func, input_data, exc_type, error_message=None):
    reader = Reader(input_data)

    with pytest.raises(exc_type) as e:
        load_func(reader)

    if error_message is not None:
        assert str(e.value) == error_message

    # No data consumed if parsing continues
    if exc_type is _ContinueLoading:
        assert list(reader) == list(input_data)


@pytest.mark.parametrize(
    "input_data,expected_data",
    [
        ("foo", "foo"),
        ("  foo bar  ", "foo bar  "),
        (" \v\t\nfoo", "foo"),
    ],
)
def test_discard_whitespaces(input_data, expected_data):
    reader = Reader(input_data)
    assert discard_whitespaces(reader) is None
    assert list(reader) == list(expected_data)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("123456", "123456", ""),
        ("789_remaining", "789", "_remaining"),
        ("123.456", "123", ".456"),
        ("1.0", "1", ".0"),
        ("123.", "123", "."),
    ],
)
def test_load_digits(input_data, result, remaining_data):
    check_load_function(load_digits, input_data, result, remaining_data)


@pytest.mark.parametrize("input_data", ["abc123", "", "-"])
def test_load_digits_error(input_data):
    check_load_function_error(load_digits, input_data, _ContinueLoading)


@pytest.mark.parametrize(
    "input_data,result,value_type,remaining_data",
    [
        ("123456", 123456, int, ""),
        ("-789_remaining", -789, int, "_remaining"),
        ("123.456", 123.456, float, ""),
        ("-1.0", -1.0, float, ""),
    ],
)
def test_load_number(input_data, result, value_type, remaining_data):
    value = check_load_function(load_number, input_data, result, remaining_data)
    assert type(value) is value_type


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ("abc123", _ContinueLoading, ""),
        ("", _ContinueLoading, ""),
        ("-", LoadError, "unexpected end of input at line 1 colum 1, expected a digit"),
        ("123.", LoadError, "unexpected end of input at line 1 colum 4, expected a digit"),
        ("-3.", LoadError, "unexpected end of input at line 1 colum 3, expected a digit"),
    ],
)
def test_load_number_error(input_data, exc_type, error_message):
    check_load_function_error(load_number, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ('"abc def"', "abc def", ""),
        ('"abc def" remaining', "abc def", " remaining"),
        ('""', "", ""),
        (
            r'"test with \"special\" characters like \"\\\""',
            'test with "special" characters like "\\"',
            "",
        ),
    ],
)
def test_load_string(input_data, result, remaining_data):
    check_load_function(load_string, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ("'abc def'", _ContinueLoading, ""),
        ('abc"def"', _ContinueLoading, ""),
        ("", _ContinueLoading, ""),
        (
            '"abc\ndef"',
            LoadError,
            "unexpected character '\\n' at line 2 colum 0, character is not allowed in string",
        ),
        (
            '"abc\\ndef"',
            LoadError,
            "unexpected character 'n' at line 1 colum 5, expected one of '\"', '\\\\'",
        ),
        ('"abc\\"', LoadError, "unexpected end of input at line 1 colum 6, expected '\"'"),
        ('"', LoadError, "unexpected end of input at line 1 colum 1, expected '\"'"),
        ('"abc', LoadError, "unexpected end of input at line 1 colum 4, expected '\"'"),
    ],
)
def test_load_string_error(input_data, exc_type, error_message):
    check_load_function_error(load_string, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("foo123/456", "foo123/456", ""),
        ("*foo", "*foo", ""),
        ("foo+bar remaining", "foo+bar", " remaining"),
    ],
)
def test_load_token(input_data, result, remaining_data):
    check_load_function(load_token, input_data, result, remaining_data)


@pytest.mark.parametrize("input_data", ["+foo", ""])
def test_load_token_error(input_data):
    check_load_function_error(load_token, input_data, _ContinueLoading)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        (":dGVzdA==:", b"test", ""),
        (":dGVzdA==:remaining", b"test", "remaining"),
        (":+/+/:", b"\xfb\xff\xbf", ""),
        ("::", b"", ""),
    ],
)
def test_load_bytes(input_data, result, remaining_data):
    check_load_function(load_bytes, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ("", _ContinueLoading, ""),
        ("dGVzdA==", _ContinueLoading, ""),
        (":", LoadError, "unexpected end of input at line 1 colum 1, expected ':'"),
        (":dGVzdA==", LoadError, "unexpected end of input at line 1 colum 9, expected ':'"),
        (
            ":abc:",
            LoadError,
            "unexpected character ':' at line 1 colum 5, invalid base64 string: Incorrect padding",
        ),
        (
            ":dGVzd)==:",
            LoadError,
            "unexpected character ')' at line 1 colum 7, character is not allowed in base64 string",
        ),
    ],
)
def test_load_bytes_error(input_data, exc_type, error_message):
    check_load_function_error(load_bytes, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("?0", False, ""),
        ("?1remaining", True, "remaining"),
    ],
)
def test_load_boolean(input_data, result, remaining_data):
    check_load_function(load_boolean, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ("", _ContinueLoading, ""),
        ("0?", _ContinueLoading, ""),
        ("?", LoadError, "unexpected end of input at line 1 colum 1, expected one of '0', '1'"),
        ("?3", LoadError, "unexpected character '3' at line 1 colum 1, expected one of '0', '1'"),
        ("?a", LoadError, "unexpected character 'a' at line 1 colum 1, expected one of '0', '1'"),
        ("??", LoadError, "unexpected character '?' at line 1 colum 1, expected one of '0', '1'"),
    ],
)
def test_load_boolean_error(input_data, exc_type, error_message):
    check_load_function_error(load_boolean, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("@1659578233", datetime(2022, 8, 4, 1, 57, 13, tzinfo=UTC), ""),
        ("@-1659578233 remaining", datetime(1917, 5, 30, 22, 2, 47, tzinfo=UTC), " remaining"),
        ("@0", datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC), ""),
    ],
)
def test_load_date(input_data, result, remaining_data):
    check_load_function(load_date, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ("", _ContinueLoading, ""),
        ("1659578233", _ContinueLoading, ""),
        ("@", LoadError, "unexpected end of input at line 1 colum 1, expected a digit"),
        ("@foo", LoadError, "unexpected character 'f' at line 1 colum 1, expected a digit"),
        (
            "@1659578233.456",
            LoadError,
            "unexpected character '.' at line 1 colum 15, decimal number is not accepted as a date",
        ),
    ],
)
def test_load_date_error(input_data, exc_type, error_message):
    check_load_function_error(load_date, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ('%"abc def"', "abc def", ""),
        ('%"abc def" remaining', "abc def", " remaining"),
        ('%""', "", ""),
        (
            '%"test with %22special%22 characters like \\, %25 or %c3%a9"',
            'test with "special" characters like \\, % or é',
            "",
        ),
        ('%"abc\\"', "abc\\", ""),
    ],
)
def test_load_display_string(input_data, result, remaining_data):
    check_load_function(load_display_string, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ('"abc def"', _ContinueLoading, ""),
        ("", _ContinueLoading, ""),
        (
            '%"abc\ndef"',
            LoadError,
            "unexpected character '\\n' at line 2 colum 0, character is not allowed in display string",
        ),
        ("%", LoadError, "unexpected end of input at line 1 colum 1, expected '\"'"),
        ('%"', LoadError, "unexpected end of input at line 1 colum 2, expected '\"'"),
        ('%"abc', LoadError, "unexpected end of input at line 1 colum 5, expected '\"'"),
        ("%'abc'", LoadError, "unexpected character \"'\" at line 1 colum 1, expected '\"'"),
        ("%abc", LoadError, "unexpected character 'a' at line 1 colum 1, expected '\"'"),
        ('%"abc%"', LoadError, "unexpected character '\"' at line 1 colum 6, expected an hexadecimal digit"),
        ('%"abc%x"', LoadError, "unexpected character 'x' at line 1 colum 6, expected an hexadecimal digit"),
        (
            '%"abc%0x"',
            LoadError,
            "unexpected character 'x' at line 1 colum 7, expected an hexadecimal digit",
        ),
        (
            '%"abc%xx"',
            LoadError,
            "unexpected character 'x' at line 1 colum 6, expected an hexadecimal digit",
        ),
    ],
)
def test_load_display_string_error(input_data, exc_type, error_message):
    check_load_function_error(load_display_string, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("123.456", 123.456, ""),
        ('"foobar"; foo=1;test="bar"', "foobar", '; foo=1;test="bar"'),
        ("*token", "*token", ""),
        (":dGVzdA==:", b"test", ""),
        ("?1", True, ""),
        ("@0", datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC), ""),
        ('%"50%e2%82%AC"', "50€", ""),
        ("30; 123", 30, "; 123"),
    ],
)
def test_load_bare_item(input_data, result, remaining_data):
    check_load_function(load_bare_item, input_data, result, remaining_data)


def test_load_bare_item_error():
    check_load_function_error(load_bare_item, "+30", _ContinueLoading, "")


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("foo123", "foo123", ""),
        ("*foo", "*foo", ""),
        ("foo_bar remaining", "foo_bar", " remaining"),
        ("foo-bar", "foo-bar", ""),
        ("foo.bar", "foo.bar", ""),
    ],
)
def test_load_key(input_data, result, remaining_data):
    check_load_function(load_key, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data",
    ["FOO", "+foo", "123foo", ""],
)
def test_load_key_error(input_data):
    check_load_function_error(load_key, input_data, _ContinueLoading)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        (';key="value"', {"key": "value"}, ""),
        (';key="value";   key2;key3=0;key3=123  foo', {"key": "value", "key2": True, "key3": 123}, "  foo"),
        ("", {}, ""),
        ("foo", {}, "foo"),
    ],
)
def test_load_parameters(input_data, result, remaining_data):
    check_load_function(load_parameters, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        (";", "unexpected end of input at line 1 colum 1, expected a key"),
        (
            ";123",
            "unexpected character '1' at line 1 colum 1, expected a key",
        ),
        (";key=", "unexpected end of input at line 1 colum 5, expected a value"),
    ],
)
def test_load_parameters_error(input_data, error_message):
    check_load_function_error(load_parameters, input_data, LoadError, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("123.456", (123.456, {}), ""),
        ('"foobar"; foo=1;test="bar" remaining', ("foobar", {"foo": 1, "test": "bar"}), " remaining"),
        ("*token", ("*token", {}), ""),
        (":dGVzdA==:", (b"test", {}), ""),
        ("?1", (True, {}), ""),
        ("@0", (datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC), {}), ""),
        ('%"50%e2%82%AC"', ("50€", {}), ""),
    ],
)
def test_load_item(input_data, result, remaining_data):
    check_load_function(load_item, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ("+30", _ContinueLoading, ""),
        ("30; 123", LoadError, "unexpected character '1' at line 1 colum 4, expected a key"),
    ],
)
def test_load_item_error(input_data, exc_type, error_message):
    check_load_function_error(load_item, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ('(123  "test" ?0)', ([(123, {}), ("test", {}), (False, {})], {}), ""),
        (
            '(123;param=1 456); foo="bar"; value=2',
            ([(123, {"param": 1}), (456, {})], {"foo": "bar", "value": 2}),
            "",
        ),
        ("()", ([], {}), ""),
        ("(\t123.456  )remaining", ([(123.456, {})], {}), "remaining"),
    ],
)
def test_load_inner_list(input_data, result, remaining_data):
    check_load_function(load_inner_list, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ("", _ContinueLoading, ""),
        ("123", _ContinueLoading, ""),
        ("(", LoadError, "unexpected end of input at line 1 colum 1, expected ')'"),
        ("(foo ", LoadError, "unexpected end of input at line 1 colum 5, expected an item"),
        ("((123))", LoadError, "unexpected character '(' at line 1 colum 1, expected an item"),
        ("(123, 456)", LoadError, "unexpected character ',' at line 1 colum 4, expected ')' or space"),
        ("(]", LoadError, "unexpected character ']' at line 1 colum 1, expected an item"),
        ("(123remaining)", LoadError, "unexpected character 'r' at line 1 colum 4, expected ')' or space"),
        ("(123 +456)", LoadError, "unexpected character '+' at line 1 colum 5, expected an item"),
        ("(123;456)", LoadError, "unexpected character '4' at line 1 colum 5, expected a key"),
    ],
)
def test_load_inner_list_error(input_data, exc_type, error_message):
    check_load_function_error(load_inner_list, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("123.456", (123.456, {}), ""),
        ("*token", ("*token", {}), ""),
        ('(123  "test" ?0)', ([(123, {}), ("test", {}), (False, {})], {}), ""),
        ('"foobar"; foo=1', ("foobar", {"foo": 1}), ""),
        ("(123;param=1); value=2", ([(123, {"param": 1})], {"value": 2}), ""),
    ],
)
def test_load_item_or_inner_list(input_data, result, remaining_data):
    check_load_function(load_item_or_inner_list, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,exc_type,error_message",
    [
        ("+30", _ContinueLoading, ""),
        ("30; 123", LoadError, "unexpected character '1' at line 1 colum 4, expected a key"),
        ("(30; 123)", LoadError, "unexpected character '1' at line 1 colum 5, expected a key"),
        ("(30); 123", LoadError, "unexpected character '1' at line 1 colum 6, expected a key"),
    ],
)
def test_load_item_or_inner_list_error(input_data, exc_type, error_message):
    check_load_function_error(load_item_or_inner_list, input_data, exc_type, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("123", [(123, {})], ""),
        ("123 456", [(123, {})], "456"),
        ("123; foo=456", [(123, {"foo": 456})], ""),
        ('123 , ("test" "foo"), token  ', [(123, {}), ([("test", {}), ("foo", {})], {}), ("token", {})], ""),
        ("", [], ""),
    ],
)
def test_load_list(input_data, result, remaining_data):
    check_load_function(load_list, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        ("  123", "unexpected character ' ' at line 1 colum 0, expected an item"),
        (", 123", "unexpected character ',' at line 1 colum 0, expected an item"),
        ("123,", "unexpected end of input at line 1 colum 4, consider removing trailing comma"),
        ("+123", "unexpected character '+' at line 1 colum 0, expected an item"),
        ("123, +456", "unexpected character '+' at line 1 colum 5, expected an item"),
        ("123;456", "unexpected character '4' at line 1 colum 4, expected a key"),
    ],
)
def test_load_list_error(input_data, error_message):
    check_load_function_error(load_list, input_data, LoadError, error_message)


@pytest.mark.parametrize(
    "input_data,result,remaining_data",
    [
        ("key1=123", {"key1": (123, {})}, ""),
        ("key1=123 456", {"key1": (123, {})}, "456"),
        ("key1=123, key1=456, key2", {"key1": (456, {}), "key2": (True, {})}, ""),
        ("key1=123; foo=456, key2;bar=0", {"key1": (123, {"foo": 456}), "key2": (True, {"bar": 0})}, ""),
        (
            'num=123 , *args=("test" "foo"), comment=token  ',
            {"num": (123, {}), "*args": ([("test", {}), ("foo", {})], {}), "comment": ("token", {})},
            "",
        ),
        ("", {}, ""),
    ],
)
def test_load_dict(input_data, result, remaining_data):
    check_load_function(load_dict, input_data, result, remaining_data)


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        ("  key=123", "unexpected character ' ' at line 1 colum 0, expected a key"),
        (", key=123", "unexpected character ',' at line 1 colum 0, expected a key"),
        ("key=123,", "unexpected end of input at line 1 colum 8, consider removing trailing comma"),
        ("123", "unexpected character '1' at line 1 colum 0, expected a key"),
        ("KEY=123", "unexpected character 'K' at line 1 colum 0, expected a key"),
        ("key1=123, KEY2=456", "unexpected character 'K' at line 1 colum 10, expected a key"),
        ("key1=123;456", "unexpected character '4' at line 1 colum 9, expected a key"),
    ],
)
def test_load_dict_error(input_data, error_message):
    check_load_function_error(load_dict, input_data, LoadError, error_message)
