import os
from glass.client import Remote

remote = Remote("localhost", 8000)

@remote.capture
def test():
    return open("README.md")


print(test().read())
