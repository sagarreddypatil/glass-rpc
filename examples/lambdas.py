import os
from glass.client import Remote

remote = Remote("localhost", 8000)


@remote.capture
def apply_on_remote(func, data):
    result = list(map(func, data))
    return {"result": result, "executed_at": os.getcwd()}


def print_and_ret(x):
    print(x)
    return x


# Using with lambda
numbers = [1, 2, 3, 4, 5]
squares = apply_on_remote(lambda x: x**2, numbers)
print(f"Squares: {squares['result']}")
print(f"Computed on remote at: {squares['executed_at']}")

# Using with named function
cube_root = apply_on_remote(lambda x: round(x ** (1 / 3), 2), [8, 27, 64, 125])
print(f"Cube roots: {cube_root['result']}")
