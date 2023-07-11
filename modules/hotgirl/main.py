import sys
import shelve
import shutil

from bs4 import BeautifulSoup as bs

from pathlib import Path
from urllib.parse import unquote, urlparse
from tenacity import retry, stop_after_attempt, wait_fixed
from server.module import ModuleBase
from utils import (
    logger,
    fetch,
    filename_filter,
    multithread_fetch,
    create_thread,
    compress_dir,
    file_size_str,
    retry_log,
)
from server.config import get_config

compress_file = get_config("global", "compress")
compress_delete = get_config("global", "compress_delete")


class HotGirl(ModuleBase):
    name = "hotgirl"
    base_url = "https://hotgirl.asia/"

    def init_routes(self):
        self.add_routes("/status", self.status)
        self.add_routes("/download/<pid>", self.download)

    def start(self):
        self.init_routes()

    def get_page_url(self, pid, page=1):
        logger.info(f"正在获取 [{page}] 页数据")
        req_args = f"?p={pid}&num={page}&stype=showall"
        return f"{self.base_url}{req_args}"

    @retry(
        stop=stop_after_attempt(20), wait=wait_fixed(3), before=retry_log, reraise=True
    )
    def request(self, pid, page=1):
        return fetch(self.get_page_url(pid, page))
        # if not sys.gettrace():
        #     return fetch(f"{self.base_url}{req_args}")

        # with shelve.open("./database/hotgirl") as db:
        #     db_key = f"{pid}-{page}"
        #     if db_key in db:
        #         return db[db_key]
        #     res = fetch(f"{self.base_url}{req_args}")
        #     db[db_key] = res
        #     return res

    def get_image_urls(self, pid):
        get_html_imgs = lambda html: [
            img.get("src") for img in html.select(".galeria_img img")
        ]

        res = self.request(pid)
        html = bs(res.text, "lxml")
        filename = filename_filter(html.select_one("[itemprop=name]").text)
        image_urls = get_html_imgs(html)
        total_page = html.select(".pagination li")
        _urls = []
        if len(total_page) > 1:
            total_page = int(total_page[-1].text)
            for page in range(2, total_page + 1):
                _urls.append(self.get_page_url(pid, page))

        for res in multithread_fetch(_urls):
            html = bs(res.text, "lxml")
            image_urls += get_html_imgs(html)
            
        # check
        new_image_urls = []
        default_suffix = ""
        for img_url in image_urls:
            img_url_p = urlparse(img_url)
            img_name = Path(img_url_p.path)
            if not default_suffix and img_name.suffix:
                default_suffix = img_name.suffix
            elif default_suffix and not img_name.suffix:
                 img_name = img_name.with_suffix(default_suffix)
            elif default_suffix != img_name.suffix:
                img_name = img_name.with_suffix(img_name.suffix + default_suffix)
                
            new_image_urls.append(img_url_p._replace(path=img_name.as_posix()).geturl())   
        
        return filename, new_image_urls

    def get_tag_name(self, pid) -> str:
        req_args = f"wp-json/wp/v2/tags?post={pid}"

        json_data = fetch(f"{self.base_url}{req_args}").json()
        tag_name = ""
        if isinstance(json_data, list):
            try:
                tag_name = unquote(
                    next(filter(lambda d: d["name"] != "COSPLAY", json_data))["slug"]
                )
            except StopIteration:
                tag_name = "cosplay"

        return tag_name

    def download(self, pid):
        tag_name = self.get_tag_name(pid)
        filename, image_urls = self.get_image_urls(pid)

        output_dir = self.output_path / tag_name
        local_images_dir = output_dir / filename
        local_images_dir.mkdir(parents=True, exist_ok=True)

        logger.info(" > 获取成功 - %s" % filename)
        logger.info(" > 分类名称 - %s" % tag_name)
        logger.info(" > 图片数量 - %s" % len(image_urls))
        logger.info(" > 保存路径 - %s" % local_images_dir)
        logger.info("开始下载, 请稍等...")

        def fetch_images(_urls, _out):
            headers = {
                "Referer": "https://hotgirl.asia/"
            }
            for img_data in multithread_fetch(_urls, headers=headers):
                img_url = img_data.url
                img_name = Path(urlparse(img_url).path).name
                img_path = _out / img_name
                if img_path.exists():
                    continue
                with img_path.open("wb") as f:
                    f.write(img_data.content)
            if compress_file:
                zip_file = compress_dir(_out)
                zip_size_str = file_size_str(zip_file)

                if compress_delete:
                    shutil.rmtree(_out)

                logger.info("处理并压缩完成, 文件大小: %s" % zip_size_str)

            else:
                logger.info("处理完成")

        task_id, t = create_thread(
            fetch_images, _urls=image_urls, _out=local_images_dir
        )

        return {"task_id": task_id}


def init():
    return HotGirl()
