import os
from glass.client import Remote

remote = Remote("photon", 8000)


@remote.func
def stuff(cb):
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


def main():
    print(stuff(callback))
    print()
    remote_file = open_file()
    print(remote_file.read())


if __name__ == "__main__":
    main()
