import math
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from strufi.dump_primitives import (
    dump_bare_item,
    dump_boolean,
    dump_bytes,
    dump_date,
    dump_decimal,
    dump_dict,
    dump_inner_list,
    dump_integer,
    dump_item,
    dump_item_or_inner_list,
    dump_key,
    dump_list,
    dump_parameters,
    dump_string,
)
from strufi.exceptions import DumpError


def check_dump_function(dump_func, value, expected):
    assert "".join(dump_func(value)) == expected


def check_dump_function_error(dump_func, value, error_message):
    with pytest.raises(DumpError) as e:
        "".join(dump_func(value))

    assert str(e.value) == error_message


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "0"),
        (999_999_999_999_999, "999999999999999"),
        (-999_999_999_999_999, "-999999999999999"),
    ],
)
def test_dump_integer(value, expected):
    check_dump_function(dump_integer, value, expected)


@pytest.mark.parametrize(
    "value,error_message",
    [
        (-(10**15), "Integer -1000000000000000 is out of bounds"),
        (10**15, "Integer 1000000000000000 is out of bounds"),
    ],
)
def test_dump_integer_error(value, error_message):
    check_dump_function_error(dump_integer, value, error_message)


@pytest.mark.parametrize(
    "value,expected",
    [
        (0.0, "0.0"),
        (0.001, "0.001"),
        (0.0001, "0.0"),
        (math.pi, "3.142"),
        (999_999_999_999.999, "999999999999.999"),
        (-999_999_999_999.999, "-999999999999.999"),
    ],
)
def test_dump_decimal(value, expected):
    check_dump_function(dump_decimal, value, expected)


@pytest.mark.parametrize(
    "value,error_message",
    [
        (-1e12, "Decimal -1000000000000.0 is out of bounds"),
        (1e12, "Decimal 1000000000000.0 is out of bounds"),
        (math.nan, "Decimal nan is out of bounds"),
        (math.inf, "Decimal inf is out of bounds"),
    ],
)
def test_dump_decimal_error(value, error_message):
    check_dump_function_error(dump_decimal, value, error_message)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", '""'),
        ("foo bar", '"foo bar"'),
        (r'foo\n"bar"', r'"foo\\n\"bar\""'),
        ("foo\nbar", '%"foo%0abar"'),
        ('"tête%"', '%"%22t%c3%aate%25%22"'),
    ],
)
def test_dump_string(value, expected):
    check_dump_function(dump_string, value, expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        (b"", "::"),
        (b"test", ":dGVzdA==:"),
        (b"\xfb\xff\xbf", ":+/+/:"),
    ],
)
def test_dump_bytes(value, expected):
    check_dump_function(dump_bytes, value, expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, "?1"),
        (False, "?0"),
    ],
)
def test_dump_boolean(value, expected):
    check_dump_function(dump_boolean, value, expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        (datetime(1970, 1, 1, tzinfo=UTC), "@0"),
        (datetime(1970, 1, 1, tzinfo=ZoneInfo("Europe/Paris")), "@-3600"),
        (datetime(2022, 8, 4, 1, 57, 13, tzinfo=UTC), "@1659578233"),
        (datetime(1917, 5, 30, 22, 2, 47, tzinfo=UTC), "@-1659578233"),
        (datetime(2022, 8, 4, 1, 57, 13, 456000, tzinfo=UTC), "@1659578233"),
    ],
)
def test_dump_date(value, expected):
    check_dump_function(dump_date, value, expected)


def test_dump_date_error():
    check_dump_function_error(
        dump_date,
        datetime(1970, 1, 1),  # noqa: DTZ001
        "Cannot dump naive datetime object",
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, "?1"),
        (1, "1"),
        (1.0, "1.0"),
        ("foo", '"foo"'),
        (b"test", ":dGVzdA==:"),
        (datetime(1970, 1, 1, tzinfo=UTC), "@0"),
    ],
)
def test_dump_bare_item(value, expected):
    check_dump_function(dump_bare_item, value, expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("foo", "foo"),
        ("*f-o-o.b_a_r", "*f-o-o.b_a_r"),
    ],
)
def test_dump_key(value, expected):
    check_dump_function(dump_key, value, expected)


@pytest.mark.parametrize(
    "value,error_message",
    [
        ("", "Key cannot ben empty"),
        ("FOO", "Key must start with lowercase letter or '*', not 'F'"),
        ("fOO", "Key must contain only lowercase letters, digits, '*', '_', '-' or '.', not 'O'"),
    ],
)
def test_dump_key_error(value, error_message):
    check_dump_function_error(dump_key, value, error_message)


@pytest.mark.parametrize(
    "value,expected",
    [
        ({}, ""),
        ({"foo": 12, "bar": "test"}, ';foo=12;bar="test"'),
        ({"true": True, "false": False}, ";true;false=?0"),
    ],
)
def test_dump_parameters(value, expected):
    check_dump_function(dump_parameters, value, expected)


@pytest.mark.parametrize(
    "value,error_message",
    [
        ({"": 0}, "Key cannot ben empty"),
        ({"FOO": 0}, "Key must start with lowercase letter or '*', not 'F'"),
    ],
)
def test_dump_parameters_error(value, error_message):
    check_dump_function_error(dump_parameters, value, error_message)


@pytest.mark.parametrize(
    "value,expected",
    [
        ((True, {}), "?1"),
        ((1, {"param": 5}), "1;param=5"),
        ((b"test", {"content-type": "text/plain"}), ':dGVzdA==:;content-type="text/plain"'),
    ],
)
def test_dump_item(value, expected):
    check_dump_function(dump_item, value, expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        (([], {}), "()"),
        (([], {"param": True}), "();param"),
        (([(True, {})], {}), "(?1)"),
        (
            ([(123, {"param": 1}), (456, {})], {"foo": "bar", "value": 2}),
            '(123;param=1 456);foo="bar";value=2',
        ),
    ],
)
def test_dump_inner_list(value, expected):
    check_dump_function(dump_inner_list, value, expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        ((b"test", {"content-type": "text/plain"}), ':dGVzdA==:;content-type="text/plain"'),
        (([], {}), "()"),
        (
            ([(123, {"param": 1}), (456, {})], {"foo": "bar", "value": 2}),
            '(123;param=1 456);foo="bar";value=2',
        ),
    ],
)
def test_dump_item_or_inner_list(value, expected):
    check_dump_function(dump_item_or_inner_list, value, expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        ([], ""),
        ([(123, {})], "123"),
        ([(123, {"foo": 456})], "123;foo=456"),
        ([(123, {}), ([("test", {}), ("foo", {})], {"len": 2})], '123, ("test" "foo");len=2'),
    ],
)
def test_dump_list(value, expected):
    check_dump_function(dump_list, value, expected)


@pytest.mark.parametrize(
    "value,expected",
    [
        ({}, ""),
        ({"key1": (123, {})}, "key1=123"),
        (
            {"num": (123, {}), "*args": ([("test", {"key": 1}), ("foo", {})], {"key": 2})},
            'num=123, *args=("test";key=1 "foo");key=2',
        ),
    ],
)
def test_dump_dict(value, expected):
    check_dump_function(dump_dict, value, expected)


@pytest.mark.parametrize(
    "value,error_message",
    [
        ({"": (0, {})}, "Key cannot ben empty"),
        ({"FOO": (0, {})}, "Key must start with lowercase letter or '*', not 'F'"),
    ],
)
def test_dump_dict_error(value, error_message):
    check_dump_function_error(dump_dict, value, error_message)
