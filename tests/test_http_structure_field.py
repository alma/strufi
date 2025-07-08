import math
from datetime import UTC, datetime

import pytest

from strufi import (
    DumpError,
    LoadError,
    dump_dict,
    dump_item,
    dump_list,
    load_dict,
    load_item,
    load_list,
)


@pytest.mark.parametrize(
    "input_data,result",
    [
        ("123.456", (123.456, {})),
        ('"foobar"; foo=1;test="bar"', ("foobar", {"foo": 1, "test": "bar"})),
        ("*token", ("*token", {})),
        (":dGVzdA==:", (b"test", {})),
        ("?1", (True, {})),
        ("@0", (datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC), {})),
        ('%"50%e2%82%AC"', ("50€", {})),
    ],
)
def test_load_item(input_data, result):
    assert load_item(input_data) == result


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        ("123 456", "unexpected character '4' at line 1 colum 4, expected end of input"),
        ("", "unexpected end of input at line 1 colum 0"),
        (" \t\n", "unexpected end of input at line 2 colum 0"),
        ("+30", "unexpected character '+' at line 1 colum 0"),
        ("(30)", "unexpected character '(' at line 1 colum 0"),
    ],
)
def test_load_item_error(input_data, error_message):
    with pytest.raises(LoadError) as e:
        load_item(input_data)

    assert str(e.value) == error_message


@pytest.mark.parametrize(
    "input_data,result",
    [
        ('"foobar"; foo=1;test="bar"', ("foobar", {"foo": 1, "test": "bar"})),
        ("123 456", (123, {})),
    ],
)
def test_load_item_permissive(input_data, result):
    assert load_item(input_data, strict=False) == result


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        ("", "unexpected end of input at line 1 colum 0"),
        ("+30", "unexpected character '+' at line 1 colum 0"),
    ],
)
def test_load_item_permissive_error(input_data, error_message):
    with pytest.raises(LoadError) as e:
        load_item(input_data, strict=False)

    assert str(e.value) == error_message


@pytest.mark.parametrize(
    "input_data,result",
    [
        ("123; foo=456", [(123, {"foo": 456})]),
        ('123 , ("test" "foo"), token  ', [(123, {}), ([("test", {}), ("foo", {})], {}), ("token", {})]),
        ("", []),
        (" \t\n", []),
    ],
)
def test_load_list(input_data, result):
    assert load_list(input_data) == result


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        ("123 456", "unexpected character '4' at line 1 colum 4, expected end of input"),
        (", 123", "unexpected character ',' at line 1 colum 0, expected an item"),
        ("123,", "unexpected end of input at line 1 colum 4, consider removing trailing comma"),
        ("+123", "unexpected character '+' at line 1 colum 0, expected an item"),
        ("123, +456", "unexpected character '+' at line 1 colum 5, expected an item"),
        ("123;456", "unexpected character '4' at line 1 colum 4, expected a key"),
        ('%"fée"', "'ascii' codec can't decode byte 0xc3 in position 3: ordinal not in range(128)"),
    ],
)
def test_load_list_error(input_data, error_message):
    with pytest.raises(LoadError) as e:
        load_list(input_data)

    assert str(e.value) == error_message


@pytest.mark.parametrize(
    "input_data,result",
    [
        ('123 , ("test" "foo"), token  ', [(123, {}), ([("test", {}), ("foo", {})], {}), ("token", {})]),
        ("123 456", [(123, {})]),
    ],
)
def test_load_list_permissive(input_data, result):
    assert load_list(input_data, strict=False) == result


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        ("123,", "unexpected end of input at line 1 colum 4, consider removing trailing comma"),
        ("123;456", "unexpected character '4' at line 1 colum 4, expected a key"),
    ],
)
def test_load_list_permissive_error(input_data, error_message):
    with pytest.raises(LoadError) as e:
        load_list(input_data, strict=False)

    assert str(e.value) == error_message


@pytest.mark.parametrize(
    "input_data,result",
    [
        ("key1=123", {"key1": (123, {})}),
        ("key1=123; foo=456, key2;bar=0", {"key1": (123, {"foo": 456}), "key2": (True, {"bar": 0})}),
        (
            'num=123 , *args=("test" "foo"), comment=token  ',
            {"num": (123, {}), "*args": ([("test", {}), ("foo", {})], {}), "comment": ("token", {})},
        ),
        ("", {}),
        (" \t\n", {}),
    ],
)
def test_load_dict(input_data, result):
    assert load_dict(input_data) == result


@pytest.mark.parametrize(
    "input_data,result",
    [
        (
            'num=123 , *args=("test" "foo"), comment=token  ',
            {"num": (123, {}), "*args": ([("test", {}), ("foo", {})], {}), "comment": ("token", {})},
        ),
        ("key=123 456", {"key": (123, {})}),
        ("kEY=123", {"k": (True, {})}),
    ],
)
def test_load_dict_permissive(input_data, result):
    assert load_dict(input_data, strict=False) == result


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        ("key=123 456", "unexpected character '4' at line 1 colum 8, expected end of input"),
        (", key=123", "unexpected character ',' at line 1 colum 0, expected a key"),
        ("key=123,", "unexpected end of input at line 1 colum 8, consider removing trailing comma"),
        ("123", "unexpected character '1' at line 1 colum 0, expected a key"),
        ("KEY=123", "unexpected character 'K' at line 1 colum 0, expected a key"),
        ("kEY=123", "unexpected character 'E' at line 1 colum 1, expected end of input"),
        ("key1=123, KEY2=456", "unexpected character 'K' at line 1 colum 10, expected a key"),
        ("key1=123;456", "unexpected character '4' at line 1 colum 9, expected a key"),
        ('key=%"fée"', "'ascii' codec can't decode byte 0xc3 in position 7: ordinal not in range(128)"),
    ],
)
def test_load_dict_error(input_data, error_message):
    with pytest.raises(LoadError) as e:
        load_dict(input_data)

    assert str(e.value) == error_message


@pytest.mark.parametrize(
    "input_data,error_message",
    [
        ("key=123,", "unexpected end of input at line 1 colum 8, consider removing trailing comma"),
        ("KEY=123", "unexpected character 'K' at line 1 colum 0, expected a key"),
        ("key1=123;456", "unexpected character '4' at line 1 colum 9, expected a key"),
    ],
)
def test_load_dict_permissive_error(input_data, error_message):
    with pytest.raises(LoadError) as e:
        load_dict(input_data, strict=False)

    assert str(e.value) == error_message


@pytest.mark.parametrize(
    "value,expected",
    [
        ((True, {}), "?1"),
        ((1, {"param": 5}), "1;param=5"),
        ((b"test", {"content-type": "text/plain"}), ':dGVzdA==:;content-type="text/plain"'),
        (([(42, {}), ("test", {"param": 0})], {}), '(42 "test";param=0)'),
    ],
)
def test_dump_item(value, expected):
    assert dump_item(value) == expected


@pytest.mark.parametrize(
    "value,error_message",
    [
        ((10**15, {}), "Integer 1000000000000000 is out of bounds"),
        ((123, {"KEY": True}), "Key must start with lowercase letter or '*', not 'K'"),
    ],
)
def test_dump_item_error(value, error_message):
    with pytest.raises(DumpError) as e:
        dump_item(value)

    assert str(e.value) == error_message


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
    assert dump_list(value) == expected


@pytest.mark.parametrize(
    "value,error_message",
    [
        ([(math.nan, {})], "Decimal nan is out of bounds"),
        ([(123, {"": True})], "Key cannot ben empty"),
    ],
)
def test_dump_list_error(value, error_message):
    with pytest.raises(DumpError) as e:
        dump_list(value)

    assert str(e.value) == error_message


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
    assert dump_dict(value) == expected


@pytest.mark.parametrize(
    "value,error_message",
    [
        ({"": 0}, "Key cannot ben empty"),
        (
            {"number": (123, {"kEY": True})},
            "Key must contain only lowercase letters, digits, '*', '_', '-' or '.', not 'E'",
        ),
    ],
)
def test_dump_dict_error(value, error_message):
    with pytest.raises(DumpError) as e:
        dump_dict(value)

    assert str(e.value) == error_message
