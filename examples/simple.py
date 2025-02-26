import os
from glass.client import Remote

remote = Remote("localhost", 8000)


def enclosing():
    x = 5

    @remote.capture
    def inner():
        nonlocal x
        print(x)
        x += 5
        return x

    x = inner()
    return x

print(enclosing())
