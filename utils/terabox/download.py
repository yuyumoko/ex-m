import requests
from pathlib import Path
from urllib.parse import urlencode
from tenacity import retry, stop_after_attempt, wait_fixed
from utils import retry_log
from ..simple_download import download as simple_download

from config import (
    proxy,
    terabox_jsToken,
    del_terabox_jsToken,
    terabox_cookie,
    del_terabox_cookie,
)

proxy_enable = proxy.enable()
proxy_address = proxy.get_proxy_address()


proxies = None
if proxy_enable:
    proxies = {"http": proxy_address, "https": proxy_address}


def get_share_info(share_url: str, page: int = 1, num: int = 20, dir: str = ""):
    query = {
        "app_id": "250528",
        "web": 1,
        "channel": "dubox",
        "clienttype": 0,
        "jsToken": terabox_jsToken(),
        "page": page,
        "num": num,
        "by": "name",
        "order": "asc",
        "shorturl": Path(share_url).name[1:],
    }

    if dir:
        query["dir"] = dir
    else:
        query["root"] = 1

    headers = {
        "Cookie": terabox_cookie(),
    }
    url = "https://www.terabox.com/share/list?"
    res_data = requests.request("GET", url + urlencode(query), headers=headers).json()
    if not res_data.get("list"):
        del_terabox_jsToken()
        del_terabox_cookie()
        raise Exception("jsToken或Cookie已过期, 请重新输入")

    return res_data["list"]


def get_dlinks(share_url: str, dir: str = ""):
    urls = []
    for item in get_share_info(share_url, dir=dir):
        dlink = item.get("dlink")
        if dlink:
            urls.append(dlink)
        elif item.get("isdir") == "1":
            urls.extend(get_dlinks(share_url, item["path"]))
    return urls


@retry(stop=stop_after_attempt(20), wait=wait_fixed(3), before=retry_log, reraise=True)
def download(
    url,
    output_path: Path,
    zip_password: str = None,
    rezip: bool = False,
    del_original: bool = False,
):
    dl_links = get_dlinks(url)

    if not dl_links:
        del_terabox_jsToken()
        del_terabox_cookie()
        raise Exception("没有找到下载链接, 可能是jsToken或Cookie已过期或者错误, 请重新输入")
    return simple_download(dl_links, output_path, zip_password, rezip, del_original)
