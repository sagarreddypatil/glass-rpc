import os
from glass.client import Remote

remote = Remote("localhost", 8000)


@remote.capture
def test_fn():
    print("hello")


print(test_fn())
