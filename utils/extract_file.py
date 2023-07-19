import platform
import subprocess
from threading import Thread
from zipfile import ZipFile
from pathlib import Path

from .tools import get_path, runCommand

unrar_tool = "unrar"

if platform.system() == "Windows":
    unrar_tool = get_path("runtime", "UnRAR.exe")


def unrar(file: Path, output_path: Path, password: str = None):
    cmd = [unrar_tool, "x", "-o+", "-p" + password, str(file), str(output_path)]
    runCommand(cmd, ret_log=False)


def unzip(file: Path, output_path: Path, password: str = None):
    with ZipFile(file, "r") as zip_file:
        zip_file.extractall(output_path, pwd=password.encode())


def is_rar_file(file: Path):
    with file.open("rb") as f:
        f.seek(0)
        if f.read(6) == b"Rar!\x1a\x07":
            return True
    return False


def extract_file(file: Path, output_path: Path, password: str = None):
    output_path.mkdir(parents=True, exist_ok=True)

    if password is None:
        password = ""

    if file.suffix == ".zip":
        unzip(file, output_path, password)
    elif file.suffix == ".rar" :
        unrar(file, output_path, password)
    elif is_rar_file(file):
        rar_name = file.with_suffix(".rar")
        file.rename(rar_name)
        file = rar_name
        unrar(file, output_path, password)
    else:
        raise Exception("Unknown file type")
    
    return file, output_path