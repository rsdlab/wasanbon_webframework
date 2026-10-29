"""Git系のサービスモジュール."""
import logging
import os
import traceback
from typing import Tuple

from ..config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from ..models.ws import WS
from ..services.wasanbon_util import _generate_mgr_command
from .process_util import start_process_return_string

logger = logging.getLogger(__name__)


def build_all_rtcs_service(ws: WS, name: str) -> Tuple[int, str, str]:
    """パッケージ内のRTCをbuildする.

    $ ./mgr.py rtc build all

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    if ws == WS.dev:
        dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    else:
        dir_path = EXECUTE_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        # options = ["rtc", "build", "all", "-v"]
        options = ["module", "build"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def build_rtc_service(ws: WS, name: str, rtc_name: str) -> Tuple[int, str, str]:
    """パッケージ内のRTCをbuildする.

    $ ./mgr.py rtc build <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    if ws == WS.dev:
        dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    else:
        dir_path = EXECUTE_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["rtc", "build", rtc_name, "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def clean_all_rtcs_service(ws: WS, name: str) -> Tuple[int, str, str]:
    """パッケージ内のRTCをcleanする.

    $ /mgr.py rtc clean all

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    if ws == WS.dev:
        dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    else:
        dir_path = EXECUTE_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["rtc", "clean", "all", "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def clean_rtc_service(ws: WS, name: str, rtc_name: str) -> Tuple[int, str, str]:
    """パッケージ内のRTCをcleanする.

    $ ./mgr.py rtc clean <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    if ws == WS.dev:
        dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    else:
        dir_path = EXECUTE_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["rtc", "clean", rtc_name, "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)
