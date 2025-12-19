import math

import numpy as np


def is_valid_price(value) -> bool:
    if value is None:
        return False

    try:
        price = float(value)
    except (TypeError, ValueError):
        return False

    # reject nan and inf
    return math.isfinite(price)
    
if __name__ == '__main__':

    tests = [
        '123.45',
        '-67.89',
        'abc',
        'nan',
        float('nan'),
        'inf',
        float('inf'),
        None,
        0,
        0.0,
        np.nan,
    ]

    for t in tests:
        # print(f"{t} -> {is_valid_price(t)}")
        print(f"{repr(t):>12} -> {is_valid_price(t)}  - is_valid_price")

    # for t in tests:
    #     # print(f"{t} -> {is_valid_price(t)}")
    #     print(f"{repr(t):>12} -> {is_price_2(t)}  - is_price_2")