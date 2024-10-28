from __future__ import annotations

import random
import string


def get_random_string(
    length: int,
    *,
    lower_case: bool = True,
    upper_case: bool = True,
    digits: bool = True,
    can_start_with_digit: bool = True,
) -> str:
    """Generate random string with required length."""
    items: list[str] = []
    if lower_case:
        items += string.ascii_lowercase
    if upper_case:
        items += string.ascii_uppercase
    if digits:
        items += string.digits

    while True:
        res = "".join(random.choices(items, k=length))  # noqa: S311
        if can_start_with_digit or res[0] not in string.digits:
            return res
