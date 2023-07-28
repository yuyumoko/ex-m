import os
from server.server import run_server
from utils import logger
from config import initConfig

__version__ = "0.0.11"

if __name__ == "__main__":
    logger.info("EX-M v%s" % __version__)
    logger.info("浏览器插件: [https://greasyfork.org/scripts/471903-ex-m/code/EX-M.user.js]")
    initConfig()
    run_server()
    os.system("pause")
