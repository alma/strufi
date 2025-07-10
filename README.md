# StruFi: HTTP Structured Field Values

This library implements a parser and a serializer for [RFC 9651](https://www.rfc-editor.org/rfc/rfc9651.html) (HTTP Structured Field Values).


## Installation

Install `strufi` by running `pip install git+https://github.com/alma/strufi.git`
`strufi` package has no dependency.


## Usage

### Parser

`strufi` module exposes 3 functions to parse structured field values:

- `load_item` to parse a single item, returning the value with the parameters.
    ```pycon
    >>> import strufi
    >>> strufi.load_item('text/html; charset=utf-8')
    ('text/html', {'charset': 'utf-8'})
    ```
- `load_list` to parse a list of items, returning a list of pairs (value, parameters).
    ```pycon
    >>> strufi.load_list('text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    [('text/html', {}), ('application/xhtml+xml', {}), ('application/xml', {'q': 0.9}), ('*/*', {'q': 0.8})]
    ```
- `load_dict` to parse a map of keys:items, returning values with their parameters.
    ```pycon
    >>> strufi.load_dict('u=1, i')
    {'u': (1, {}), 'i': (True, {})}
    ```

### Serializer

The module also exposes functions for the serializing operations, which are the reverse operations of the parsing ones.

- `dump_item` takes a value with parameters and returns the structured field value representation of a single item as a string
    ```pycon
    >>> strufi.dump_item(('text/html', {'charset': 'utf-8'}))
    '"text/html";charset="utf-8"'
    ```
- `dump_list` takes a list of items and return the structured list representation
    ```pycon
    >>> strufi.dump_list([('text/html', {}), ('application/xhtml+xml', {}), ('application/xml', {'q': 0.9}), ('*/*', {'q': 0.8})])
    '"text/html", "application/xhtml+xml", "application/xml";q=0.9, "*/*";q=0.8'
    ```
- `dump_dict` takes a dictionnary of key:item and return the structured dict representation
    ```pycon
    >>> strufi.dump_dict({'u': (1, {}), 'i': (True, {})})
    'u=1, i'
    ```

## Development

### Environment

Use `pip install -e '.[dev]'` to install `strufi` with development dependencies (tests & lint) in your local (virtual) environment.

Here are the tools you can use to reproduce the checks made by the continuous integration workflow:

- `ruff format --diff` to check file format (you can run `ruff format` to apply changes)
- `ruff check` to check for specific linting rules
- `mypy .` to check for type annotations consistency
- `pytest -vv` to run tests suit

All these commands are also available through a Makefile that also takes care of the virtual environment: `make lint`, `make mypy` and `make tests`.
You could also run `make all` or simply `make` to execute the three tasks.

### Contributing

Feel free to [open issues](https://github.com/alma/strufi/issues) to report bugs or ask for features and to open pull-requests to work on existing issues.

The code of the project is published under [MIT license](https://github.com/alma/strufi/blob/main/LICENSE).

### Packaging

Build dependencies can be installed with `pip install -e '.[build]'`.

Then the package can be built with `python -m build` (or `make build`) and [uploaded on PyPI](https://pypi.org/project/strufi/) with `twine upload dist/*` (or `make upload` that builds & uploads the package).
