from datetime import datetime

type BareItem = bool | int | float | str | bytes | datetime
type Parameters = dict[str, BareItem]
type Item = tuple[BareItem, Parameters]
type ItemList = tuple[list[Item], Parameters]
