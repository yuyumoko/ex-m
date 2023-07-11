from server.server import run_server
from utils import logger

__version__ = "0.0.5"

if __name__ == "__main__":
    logger.info("EX-M v%s" % __version__)
    run_server()
