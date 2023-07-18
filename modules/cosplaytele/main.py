import werkzeug.exceptions
from bs4 import BeautifulSoup as bs
from flask import request
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_fixed
from server.module import ModuleBase
from utils import (
    logger,
    fetch,
    create_thread,
    filename_filter,
    retry_log,
)
from config import is_compress_file, is_compress_delete_file
from utils.mediafire.download import download as mf_download

compress_file = is_compress_file()
compress_delete = is_compress_delete_file()


class cosplaytele(ModuleBase):
    name = "cosplaytele"
    base_url = "https://cosplaytele.com/"

    def init_routes(self):
        self.add_routes("/status", self.status)
        self.add_routes("/download", self.start_download, methods=["POST"])

    def start(self):
        self.init_routes()

    @retry(
        stop=stop_after_attempt(20), wait=wait_fixed(3), before=retry_log, reraise=True
    )
    def request(self, url):
        return fetch(url)

    def download(self, request_url: str):
        logger.info("正在获取信息 [%s]" % request_url)

        res = self.request(request_url)
        html = bs(res.text, "lxml")
        info_html = html.select("blockquote strong")
        info_list = [x.text.split(": ") for x in info_html]
        cosplayer = filename_filter(info_list[0][1]).strip()
        zip_password = info_html[-1].find("input").get("value") or "cosplaytele"
        download_url = [
            x.get("href") for x in html.select("a") if "mediafire" in x.get("href")
        ][0]

        logger.info(f"cosplayer: [{cosplayer}]")
        logger.info(f"zip_password: [{zip_password}]")
        logger.info(f"download_url: [{download_url}]")
        logger.info("开始下载")
        mf_download(
            download_url,
            self.output_path / cosplayer,
            zip_password,
            rezip=False,
            del_original=compress_delete,
        )
        logger.info("处理完成")

    def start_download(self):
        try:
            request_data = request.get_json()
        except werkzeug.exceptions.UnsupportedMediaType:
            request_data = request.form.to_dict()
            
        request_url = request_data.get("url")
        task_id = None
        if not request_url:
            return {"error": "url is required"}

        task_id, t = create_thread(self.download, request_url=request_url)

        return {"task_id": task_id}


def init():
    return cosplaytele()
