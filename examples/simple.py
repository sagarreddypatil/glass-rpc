from glass.client import Remote

remote = Remote("localhost", 8000)


class SomeClass():
    def __init__(self):
        print("SomeClass.__init__()")

    def some_method(self, *args):
        print(f"SomeClass.some_method{args}")


obj2 = SomeClass()


@remote.func
def test_fn():
    wow = SomeClass()
    wow.some_method("A")
    print(__name__)
    obj2.some_method("B")


test_fn()
