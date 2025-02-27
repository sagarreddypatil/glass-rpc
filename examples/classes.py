import os
import time
from glass.client import Remote

remote = Remote("localhost", 8000)


# Decorate the entire class to run remotely
@remote.capture
class RemoteProcessor:
    def __init__(self):
        self.start_time = time.time()
        self.remote_cwd = os.getcwd()
        print(f"RemoteProcessor initialized at: {self.remote_cwd}")

    def process_data(self, data):
        processed = []

        for item in data:
            # Simulate processing
            time.sleep(0.1)
            processed.append(f"Processed {item}")

        return {
            "processed_items": processed,
            "remote_cwd": self.remote_cwd,
            "processing_time": time.time() - self.start_time,
        }

    def get_system_info(self):
        import platform

        return {
            "os": platform.system(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "cwd": self.remote_cwd,
        }


# Create instance of the remote class
processor = RemoteProcessor()

# All methods run remotely since the entire class is remote
result = processor.process_data(["item1", "item2", "item3"])
sys_info = processor.get_system_info()

print(f"Executed at: {result['remote_cwd']}")
print(f"Items: {result['processed_items']}")
print(f"Remote system: {sys_info['os']} at {sys_info['hostname']}")
