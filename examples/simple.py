import os
from glass.client import Remote

remote = Remote("photon", 8000)

@remote.func
def test_cb(cb):
    cb()
    return hostname()

@remote.func
def open_file():
    # file only exists on server
    return open("/etc/os-release", "r")

def callback():
    print(hostname())

def hostname():
    return os.uname()[1]

print(test_cb(callback))
print()
remote_file = open_file()
print(remote_file.read())
