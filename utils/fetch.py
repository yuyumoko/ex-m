import requests
import requests_async
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_fixed
from urllib.parse import quote, unquote, parse_qs, urlparse
from pathlib import Path
from .tools import Config
from .log import retry_log

cf = Config(Path("./config.ini").resolve())


def get_config(section: str, option: str, raw=True) -> str:
    return cf.get(section, option, raw=raw)


proxy_address = get_config("proxy", "address")
proxy_enable = get_config("proxy", "enable")
proxies = None
if proxy_enable:
    proxies = {"http": proxy_address, "https": proxy_address}


def fetch(url: str, method: str = "GET", **kwargs) -> requests.Response:
    kwargs["proxies"] = proxies
    # kwargs["verify"] = False
    return requests.request(method, url, **kwargs)


async def fetch_sync(
    url: str, method: str = "GET", **kwargs
) -> requests_async.Response:
    kwargs["proxies"] = proxies
    kwargs["verify"] = False
    return await requests_async.request(method, url, **kwargs)


def multithread_fetch(
    urls: list[str],
    method: str = "GET",
    max_workers: int = 20,
    thread_name_prefix: str = "T",
    show_progress: bool = True,
    fetch_func: callable = fetch,
    fetch_args: dict = {},
    **kwargs,
) -> list[requests_async.Response]:
    @retry(
        stop=stop_after_attempt(20), wait=wait_fixed(3), before=retry_log, reraise=True
    )
    def _fetch(url: str, method: str, pbar: tqdm, **kwargs):
        if fetch_func == fetch:
            res_data = fetch_func(url, method, **kwargs)
            if res_data.status_code != 200:
                raise Exception("获取失败")
        else:
            res_data = fetch_func(**fetch_args)
        if pbar:
            pbar.update(1)

        return res_data

    with ThreadPoolExecutor(
        max_workers=max_workers, thread_name_prefix=thread_name_prefix
    ) as executor:
        pbar = tqdm(total=len(urls)) if show_progress else None
        futures = []
        for url in urls:
            url_p = urlparse(url)
            url_path = quote(unquote(url_p.path))
            url = url.replace(url_p.path, url_path)
            
            futures.append(executor.submit(_fetch, url, method, pbar, **kwargs))

        for future in as_completed(futures):
            yield future.result()

        if pbar:
            pbar.close()
