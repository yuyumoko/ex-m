import os
from server.server import run_server
from utils import logger
from config import initConfig

__version__ = "0.0.7"

if __name__ == "__main__":
    logger.info("EX-M v%s" % __version__)
    initConfig()
    run_server()
    os.system("pause")
