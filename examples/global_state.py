import os
import random
from glass.client import Remote

remote = Remote("localhost", 8000)

# Global state that will be modified by the remote function
state = {"count": 0, "values": []}


@remote.capture
def update_remote_state(iterations=5):
    global state
    cwd = os.getcwd()

    for _ in range(iterations):
        state["count"] += 1
        state["values"].append(random.randint(1, 100))

    state["remote_path"] = cwd
    # return state


# Update state on remote machine
update_remote_state()
print(f"Count: {state['count']}")
print(f"Generated values: {state['values']}")
print(f"Remote path: {state['remote_path']}")
