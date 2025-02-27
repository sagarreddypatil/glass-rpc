from glass.client import Remote

remote = Remote("localhost", 8000)


@remote.capture
def generate_numbers(n):
    for i in range(n):
        yield i * 2

if __name__ == "__main__":
    gen = generate_numbers(5)
    for num in gen:
        print(num)

