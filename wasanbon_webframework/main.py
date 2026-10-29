"""Main Module."""

import argparse
import os
import shutil
from dataclasses import dataclass
from logging import getLogger

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from wasanbon_webframework import get_version
from wasanbon_webframework.config.config import (
    DEBUG,
    DEVELOP_WORKSPACE_BASE_PATH,
    EXECUTE_WORKSPACE_BASE_PATH,
    WW_BASE_PATH,
)
from wasanbon_webframework.services import command_util

from .middleware.auth import BasicAuth
from .middleware.logger import LoggerMiddleware
from .routers import binder, build, deploy, execution, log, nameserver, packages, version

logger = getLogger(__name__)


tags_metadata = [
    {
        "name": "default",
    },
    {
        "name": "nameserver",
        "description": "Operations to nameserver",
    },
    {
        "name": "version",
        "description": "Operations to check version",
    },
    {
        "name": "deploy",
        "description": "Operations to deploy",
    },
    {
        "name": "build",
        "description": "Operations to build",
    },
    {
        "name": "log",
        "description": "Operations to get execution log",
    },
]

# DW/EWが存在しなければ作成する。
os.makedirs(DEVELOP_WORKSPACE_BASE_PATH, exist_ok=True)
os.makedirs(EXECUTE_WORKSPACE_BASE_PATH, exist_ok=True)
user_info_path = os.path.join(WW_BASE_PATH, "user_info.yml")
if not os.path.isfile(user_info_path):
    shutil.copy2(os.path.join(os.path.dirname(__file__), "config/user_info.yml"), user_info_path)

app = FastAPI(openapi_tags=tags_metadata)
app.version = get_version()


@dataclass
class HelloWorldModel:
    """Hello World Model."""

    msg: str


@app.get(
    "/",
    tags=["default"],
    description="Hello World API.",
    response_model=HelloWorldModel,
    responses={
        status.HTTP_200_OK: {
            "content": {"application/json": {"example": {"msg": "Hello World. I am Wasanbon Webframework."}}},
        }
    },
)
def hello_world() -> HelloWorldModel:
    """テスト用サンプル関数.

    Returns:
        HelloWorldModel: テスト用サンプル返り値
    """
    return HelloWorldModel(msg="Hello World. I am Wasanbon Webframework.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggerMiddleware)
if not DEBUG:
    bkend = BasicAuth()
    app.add_middleware(AuthenticationMiddleware, backend=bkend, on_error=bkend.default_on_error)

app.include_router(deploy.router)
app.include_router(log.router)
app.include_router(build.router)
app.include_router(binder.router)
app.include_router(packages.router)
app.include_router(nameserver.router)
app.include_router(execution.router)
app.include_router(log.router)
app.include_router(version.router)


def main() -> None:
    """起動処理."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "stop", "ps", "pskill", "user_info_dist"], help="command")
    parser.add_argument("--other_hosts", action="store_true", help="launch other host's wasanbon-webframework")
    parser.add_argument("--pid", type=int, help="pid")

    args = parser.parse_args()
    if args.command == "start":
        command_util.start()

        if args.other_hosts:
            command_util.start_other_host()

    elif args.command == "stop":
        command_util.stop()

        if args.other_hosts:
            command_util.stop_other_host()

    elif args.command == "ps":
        command_util.ps()

    elif args.command == "pskill":
        if args.pid is None:
            while True:
                pid_str = input("PID: ")
                try:
                    int(pid_str)
                    break
                except BaseException:
                    print("Please input integer only")  # noqa
                    continue
        else:
            pid_str = str(args.pid)

        command_util.kill(pid_str)

    elif args.command == "user_info_dist":
        command_util.user_info_dist()
