import re
import requests
import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed
from utils import compress_dir, extract_file, retry_log


def get_mediafire(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.reddit.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    return requests.request("GET", url, headers=headers, data={})


def get_title_mf(url):
    reqs = get_mediafire(url)
    soup = BeautifulSoup(reqs.text, "html.parser")
    try:
        temp_output = str(soup.find("div", {"class": "filename"}).get_text())
    except AttributeError:
        temp_output = soup.find("meta", {"property": "og:title"}).get("content")
    return temp_output


CHUNK_SIZE = 512 * 1024  # 512KB

def extractDownloadLink(contents):
    for line in contents.splitlines():
        m = re.search(r'href="((http|https)://download[^"]+)', line)
        if m:
            return m.groups()[0]

@retry(stop=stop_after_attempt(20), wait=wait_fixed(3), before=retry_log, reraise=True)
def download(
    url,
    output_path: Path,
    zip_password: str = None,
    rezip: bool = False,
    del_original: bool = False,
):
    output_path.mkdir(parents=True, exist_ok=True)

    zip_name = get_title_mf(url)
    output_file = output_path / zip_name

    sess = requests.session()
    while True:
        res = sess.get(url, stream=True)
        if "Content-Disposition" in res.headers:
            # This is the file
            break

        # Need to redirect with confiramtion
        url = extractDownloadLink(res.text)

        if url is None:
            raise Exception("Unable to find download link")

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
        f.close()

    except IOError as e:
        raise Exception("Unable to write file") from e

    output_file, _ = extract_file(output_file, output_path, zip_password)

    if del_original:
        output_file.unlink()
        output_file = output_file.with_suffix("")
    if rezip:
        output_file = compress_dir(output_path)

    return output_file
