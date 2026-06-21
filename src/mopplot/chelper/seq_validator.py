# created by lesomras on 2026-6-12

from mopplot.exceptions import InvalidValueException
from typing import Callable, Any


def seq_validator(
    item_validator: Callable[[Any], Any], raise_error=True
) -> Callable[[list], bool]:
    def validator(seq: list) -> bool:
        for item in seq:
            try:
                item_validator(item)
            except Exception as e:
                if raise_error:
                    raise InvalidValueException(
                        f"Item {item!r} failed sequence validator"
                    ) from e
                return False
        return True

    return validator
