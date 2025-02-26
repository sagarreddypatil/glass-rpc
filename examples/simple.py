import os
from glass.client import Remote

remote = Remote("localhost", 8000)


class BaseClass:
    def __init__(self):
        print(os.getcwd())


@remote.capture
class Thingy(BaseClass):
    def __init__(self, x):
        super().__init__()
        self.x = x
        self.cwd = os.getcwd()

    def stuff(self):
        return self.cwd

    def __call__(self, y):
        return self.x + y


@remote.capture
def test():
    os.chdir("/tmp")
    return os.listdir(os.getcwd())


remote_obj = Thingy(123)
print(remote_obj.stuff())
print(remote_obj(456))
print(fib(10))
