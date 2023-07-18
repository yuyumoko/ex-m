import os
import re
import sys
import hashlib
import inspect
import subprocess

from tqdm import tqdm
from zipfile import ZipFile
from threading import Thread
from pathlib import Path
from .simple_config import SimpleConfig


def get_path(*paths):
    return os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), *paths)


def md5(context):
    return hashlib.md5(context).hexdigest()


def str2md5(s):
    return md5(str(s).encode())


class Config(SimpleConfig):
    ...


def filename_filter(filename: str) -> str:
    return re.sub(r"[\/\\\:\*\?\"\<\>\|]", "_", filename)


def get_func_key(func, *fn_args, **fn_kwargs):
    bound = inspect.signature(func).bind(*fn_args, **fn_kwargs)
    bound.apply_defaults()
    bound.arguments.pop("self", None)
    return str2md5(f"{func.__name__}@{bound.arguments}")


def create_thread(func: callable, task_id: str = None, *args, **kwargs):
    if task_id is None:
        task_id = get_func_key(func, *args, **kwargs)
    t = Thread(target=func, args=args, kwargs=kwargs, name=task_id)
    t.setDaemon(True)
    t.start()
    return task_id, t


def compress_dir(
    dir_path: Path,
    zip_path: Path = None,
    show_progress: bool = True,
):
    if zip_path is None:
        zip_path = dir_path.parent / (dir_path.name + ".zip")

    files = list(dir_path.glob("**/*"))
    pbar = tqdm(total=len(files)) if show_progress else None

    with ZipFile(zip_path, "w") as zip_file:
        for file in files:
            zip_file.write(file, file.relative_to(dir_path))
            if pbar:
                pbar.update(1)

    if pbar:
        pbar.close()
    return zip_path


def size_format(size):
    if size < 1000:
        return "%i" % size + "B"
    elif 1000 <= size < 1000000:
        return "%.1f" % float(size / 1000) + "KB"
    elif 1000000 <= size < 1000000000:
        return "%.1f" % float(size / 1000000) + "MB"
    elif 1000000000 <= size < 1000000000000:
        return "%.1f" % float(size / 1000000000) + "GB"
    elif 1000000000000 <= size:
        return "%.1f" % float(size / 1000000000000) + "TB"


def file_size_str(path):
    return size_format(os.stat(path).st_size)


def runCommand(command, callback: callable = None, ret_log: bool = True):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log = []
    line_num = 0
    # 实时获取输出
    while True:
        output = process.stdout.readline() or process.stderr.readline()
        return_code = process.poll()

        if not output and return_code is not None:
            break
        elif not output and return_code == 0:
            break
        elif output and ret_log:
            line = output.decode("utf-8", "ignore").strip()
            log.append(line)
            if callback:
                if callback(line, line_num):
                    process.wait()
                    break
            else:
                print(line)
            line_num += 1

    return log