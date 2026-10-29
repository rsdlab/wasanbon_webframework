"""Git系のサービスモジュール."""
import logging
import os
import traceback
import zipfile
from io import BytesIO
from typing import List, Tuple

from fastapi.responses import StreamingResponse

from ..config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from ..models.ws import WS

logger = logging.getLogger(__name__)


def make_zipfile_as_streaming_response(ws: WS, name: str, file_list: List[str]) -> StreamingResponse:
    """RTCごとにログファイルをzipでまとめて取得する.

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名
        file_list(List(str)): ログファイル名一覧

    Returns:
        StreamingResponse: zipファイル
    """
    # パッケージのディレクトリに移動する
    if ws == WS.dev:
        dir_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/log"
    else:
        dir_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}/log"
    os.chdir(dir_path)

    io = BytesIO()
    zip_filename = f"{name}_log.zip"
    with zipfile.ZipFile(io, mode="w", compression=zipfile.ZIP_DEFLATED) as zip:
        for fpath in file_list:
            zip.write(fpath)

    os.chdir(home_dir)

    return StreamingResponse(
        iter([io.getvalue()]),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment;filename={zip_filename}"},
    )


def get_log_file_list(ws: WS, name: str) -> Tuple[int, List[str]]:
    """対象ディレクトリのファイル一覧を取得する.

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名

    Returns:
        List(str): ログファイル名一覧
    """
    # パッケージ/logディレクトリ配下のファイル一覧を取得する
    if ws == WS.dev:
        log_file_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/log"
    else:
        log_file_path = f"{EXECUTE_WORKSPACE_BASE_PATH}/{name}/log"

    try:
        os.chdir(log_file_path)
        # パッケージ/logディレクトリ配下のファイル一覧を取得する
        log_file_list = os.listdir(log_file_path)
        code = 0
        os.chdir(home_dir)
    except FileNotFoundError:
        log_file_list = [traceback.format_exc()]
        code = 1

    return code, log_file_list
