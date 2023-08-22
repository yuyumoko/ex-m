import re
import requests
import tqdm
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_fixed
from urllib.parse import unquote
from utils import logger, compress_dir, extract_file, retry_log, filename_filter
from config import proxy

proxy_enable = proxy.enable()
proxy_address = proxy.get_proxy_address()


proxies = None
if proxy_enable:
    proxies = {"http": proxy_address, "https": proxy_address}

CHUNK_SIZE = 512 * 1024  # 512KB


@retry(stop=stop_after_attempt(20), wait=wait_fixed(3), before=retry_log, reraise=True)
def download(
    download_urls: list[str],
    output_path: Path,
    zip_password: str = None,
    rezip: bool = False,
    del_original: bool = False,
):
    output_path.mkdir(parents=True, exist_ok=True)
    sess = requests.session()

    for dl_link in download_urls:
        res = sess.get(dl_link, stream=True, proxies=proxies)
        
        filename = re.findall("=(UTF-8)?(.+)", res.headers["Content-Disposition"])[0][-1]
        filename = unquote(filename.strip('"').strip("'"))
        filename = filename_filter(filename.encode("ISO-8859-1").decode())

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

        if zip_password is not None:
            logger.info("正在解压: [%s]" % output_file.name)
            output_file, _ = extract_file(output_file, output_path, zip_password)

        if del_original:
            output_file.unlink()
            output_file = output_file.with_suffix("")

        if rezip:
            output_file = compress_dir(output_path)

    return output_file
