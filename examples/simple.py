import os
from glass.client import Remote

remote = Remote("localhost", 8000)

@remote.capture
def automation():
    # does somethings
    return os.listdir(os.getcwd())


print(automation())