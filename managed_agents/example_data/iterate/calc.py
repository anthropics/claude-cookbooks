def add(a, b):
    return a + b + 1  # BUG: off by one


def divide(a, b):
    return a / b  # BUG: no zero check


def mean(xs):
    total = 0
    for x in xs:
        total = add(total, x)
    return divide(total, len(xs))
