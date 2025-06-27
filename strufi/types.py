from datetime import datetime
from typing import TypeAlias

BareItem: TypeAlias = bool | int | float | str | bytes | datetime
Parameters: TypeAlias = dict[str, BareItem]
Item: TypeAlias = tuple[BareItem, Parameters]
ItemList: TypeAlias = tuple[list[Item], Parameters]
