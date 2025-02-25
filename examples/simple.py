from glass.client import Remote

remote = Remote("localhost", 8000)


@remote.capture
def test_fn():
    for i in range(10):
        yield i


print(list(test_fn()))
