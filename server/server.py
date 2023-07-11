import sys

import typing as t
from pathlib import Path
from flask import Flask, Response, abort, jsonify, request
from flask_cors import CORS
from werkzeug.serving import WSGIRequestHandler
from utils import get_path, logger
from .module import ModuleBase

from .config import get_config


if not sys.gettrace():
    WSGIRequestHandler.log_request = lambda *args: None

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
CORS(app, resources=r"/*")

MODULES: t.Dict[str, list[ModuleBase]] = {}


@app.route("/status", methods=["GET"])
def check_md5():
    ret = {"retcode": 0, "msg": "ok"}
    return jsonify(ret)


def handle_modules():
    modules_path = Path(get_path("modules"))
    for module_path in modules_path.glob("*"):
        if module_path.is_dir():
            module_name = module_path.name
            module_main = "modules.%s.main" % module_name
            module = __import__(module_main, fromlist=[module_main])
            module: ModuleBase = getattr(module, "init")()
            if not isinstance(module, ModuleBase):
                logger.error(" -load module [%s] failed" % module_name)
                continue

            module.start()
            MODULES[module_name] = module
            for route in module.url_routes:
                app.add_url_rule(**route)

            logger.info(" +load module [%s]" % module_name)
        else:
            continue


def run_server():
    server_host = get_config("global", "server_host")
    server_port = get_config("global", "server_port")
    handle_modules()

    if sys.gettrace():
        app.run(host=server_host, port=server_port)
    else:
        from gevent import pywsgi

        from utils import logger

        logger.info("server start at %s:%s" % (server_host, server_port))
        server = pywsgi.WSGIServer((server_host, int(server_port)), app, log=None)
        server.serve_forever()
