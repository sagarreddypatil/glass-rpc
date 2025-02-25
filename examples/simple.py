import os
from glass.client import Remote, host_func

remote = Remote("localhost", 8000)


@host_func
def host_print(*args):
    print(*args)


@remote.func
def test_fn():
    host_print(os.getcwd())
    host_print(__name__)


test_fn()
