import os
import socket
import logging
from .serdes import Serializer
from .bidirpc import BidirPC
from .util import fmt_args_kwargs

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s][%(process)d] %(asctime)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)



if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: server.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        pid = os.fork()
        if pid == 0:
            pid = os.getpid()
            logger.info(f"connection accepted from {addr}")
            HOME = os.environ["HOME"]
            logger.info(f"setting workdir to {HOME}")
            os.chdir(HOME)
            rpc = BidirPC()
            rpc.connect(conn)
            ser = Serializer(rpc)
            while True:
                try:
                    rpc.recv()
                except EOFError:
                    logger.info("connection closed")
                    break
                except Exception as e:
                    rpc.exception(e)

            conn.close()
            os._exit(0)
        else:
            conn.close()
