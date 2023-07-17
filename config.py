from pathlib import Path
from utils.arg_require import ArgRequire, ArgRequireOption


ag = ArgRequire(ArgRequireOption(save=True, save_path="config.ini"))


@ag.apply(True, "请输入下载目录")
def get_download_path(download_path: Path):
    if not download_path.exists():
        raise ValueError("下载目录不存在")
    return download_path


@ag.apply(True, ("是否压缩下载的文件(y/n)", True))
def is_compress_file(compress: bool):
    return compress


@ag.apply(True, ("压缩文件后是否删除临时文件夹(y/n)", True))
def is_compress_delete_file(compress_delete: bool):
    return compress_delete


class proxy:
    @ag.apply(True, ("是否启用代理(y/n)", True))
    @staticmethod
    def enable(enable_proxy: bool):
        if enable_proxy:
            proxy.get_proxy_address()
        return enable_proxy

    @ag.apply(True, ("请输入代理地址", "http://127.0.0.1:7890"))
    @staticmethod
    def get_proxy_address(proxy_address: str):
        return proxy_address


def initConfig():
    get_download_path()
    is_compress_file()
    is_compress_delete_file()
    proxy.enable()
