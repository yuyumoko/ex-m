import typing as t

from pathlib import Path
from pydantic import BaseModel
from functools import wraps
from inspect import iscoroutinefunction
from abc import ABC, abstractmethod
from .config import get_config


__all__ = ["ModuleBase"]


# class ModuleOption(BaseModel):
#     name: str
#     description: str = ""


class ModuleResponse(BaseModel):
    retcode: int = 0
    msg: str = "ok"
    data: t.Any = None


output_path = get_config("global", "download_path")


class ModuleBase(ABC):
    name = ""
    base_url = ""
    description = ""
    url_routes = []

    output_path = Path(output_path)

    @abstractmethod
    def start(self):
        ...

    def add_routes(
        self,
        rule: str,
        view_func: t.Callable,
        endpoint: str = None,
        methods: list[str] = ["GET"],
    ):
        @wraps(view_func)
        async def wrapper(*args, **kwargs):
            if iscoroutinefunction(view_func):
                res = await view_func(*args, **kwargs)
            else:
                res = view_func(*args, **kwargs)

            if res is None:
                return ModuleResponse().dict()
            return ModuleResponse(data=res).dict()

        self.url_routes.append(
            {
                "rule": f"/{self.name}{rule}",
                "endpoint": endpoint,
                "view_func": wrapper,
                "methods": methods,
            }
        )

    def status(self):
        return {
            "name": self.name,
            "base_url": self.base_url,
            "description": self.description,
        }
