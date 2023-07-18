import platform
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


def extract_file(file: Path, output_path: Path, password: str = None):
    output_path.mkdir(parents=True, exist_ok=True)

    if password is None:
        password = ""

    if file.suffix == ".zip":
        unzip(file, output_path, password)
    elif file.suffix == ".rar":
        unrar(file, output_path, password)
    else:
        raise Exception("Unknown file type")
