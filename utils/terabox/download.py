import re
import requests
import tqdm
from pathlib import Path
from urllib.parse import urlencode
from tenacity import retry, stop_after_attempt, wait_fixed
from utils import compress_dir, extract_file, retry_log

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


def get_share_info(share_url: str, page: int = 1, num: int = 20):
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
        "root": 1,
    }
    headers = {
        "Cookie": terabox_cookie(),
    }
    url = "https://www.terabox.com/share/list?"
    return requests.request("GET", url + urlencode(query), headers=headers).json()


CHUNK_SIZE = 512 * 1024  # 512KB


@retry(stop=stop_after_attempt(20), wait=wait_fixed(3), before=retry_log, reraise=True)
def download(
    url,
    output_path: Path,
    zip_password: str = None,
    rezip: bool = False,
    del_original: bool = False,
):
    share_info = get_share_info(url)
    if not share_info.get("list"):
        del_terabox_jsToken()
        del_terabox_cookie()
        raise Exception("jsToken或Cookie已过期, 请重新输入")

    dl_links = [x["dlink"] for x in share_info["list"] if x.get("dlink")]
    if not dl_links:
        del_terabox_jsToken()
        del_terabox_cookie()
        raise Exception("没有找到下载链接, 可能是jsToken或Cookie已过期或者错误, 请重新输入")

    output_path.mkdir(parents=True, exist_ok=True)

    sess = requests.session()

    for dl_link in dl_links:
        res = sess.get(dl_link, stream=True, proxies=proxies)
        compiler = re.compile(r"filename=(.*)")
        filename = (
            compiler.search(res.headers["Content-Disposition"]).group(1).strip('"')
        )
        filename = filename.encode("ISO-8859-1").decode()

        output_file = output_path / filename

        f = output_file.open("wb")

        try:
            total = res.headers.get("Content-Length")

            if total is not None:
                total = int(total)

            pbar = tqdm.tqdm(total=total, unit="B", unit_scale=True)
            for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)

                pbar.update(len(chunk))

            pbar.close()

        except IOError as e:
            raise Exception("Unable to write file") from e
        finally:
            f.close()

    output_file, _ = extract_file(output_file, output_path, zip_password)

    if del_original:
        output_file.unlink()
        output_file = output_file.with_suffix("")
    if rezip:
        output_file = compress_dir(output_path)

    return output_file
