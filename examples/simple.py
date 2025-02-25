import os
from glass.client import Remote

remote = Remote("localhost", 8000)


@remote.capture
def test_fn():
    return open("/Users/sagar/.zshrc", "r")

print(test_fn().read())