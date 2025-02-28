import os
import time
from glass.client import Remote

remote = Remote("localhost", 8000)


class RemoteProcessor:
    def __init__(self, name):
        self.name = name
        self.start_time = time.time()

    @remote.capture # this is not supported
    def process_data(self, data):
        processed = []
        cwd = os.getcwd()

        for item in data:
            # Simulate processing
            time.sleep(0.1)
            processed.append(f"Processed {item}")

        return {
            "name": self.name,
            "processed_items": processed,
            "remote_cwd": cwd,
            "processing_time": time.time() - self.start_time,
        }


# Using a class with remote method
def main():
    processor = RemoteProcessor("DataHandler")
    result = processor.process_data(["item1", "item2", "item3"])

    print(f"Processor: {result['name']}")
    print(f"Executed at: {result['remote_cwd']}")
    print(f"Items: {result['processed_items']}")

if __name__ == "__main__":
    main()
