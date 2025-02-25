import os
from glass.client import Remote

remote = Remote("localhost", 8000)


@remote.func
def stuff(f):
    return f.read()


def main():
    print(stuff(open("pyproject.toml", "r")))
    pass


if __name__ == "__main__":
    main()
