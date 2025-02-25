import os
from glass.client import Remote

remote = Remote("localhost", 8000)


@remote.func
def hostname():
    return os.uname().nodename


def main():
    print(hostname())
    pass


if __name__ == "__main__":
    main()
