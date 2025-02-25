from os import getcwd, listdir, chdir
from glass.client import Remote

remote = Remote("localhost", 8000)

@remote.capture
def test():
    chdir("/tmp")
    return listdir(getcwd()), getcwd()


print(test())
