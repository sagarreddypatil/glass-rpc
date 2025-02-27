import os
from glass.client import Remote

remote = Remote("localhost", 8000)


class Container:
    def __init__(self, x):
        self.x = x


def enclosing():
    xc = Container(5)

    @remote.capture
    def inner():
        nonlocal xc
        xc.x += 5

    inner()
    return xc.x


print(enclosing())
