"""binder系のサービスモジュール."""

import os
import traceback
from typing import Dict, Optional, Tuple

import yaml

from ..config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from ..models.ws import WS
from ..services.wasanbon_util import _generate_mgr_command, _generate_wasanbon_admin_command
from .process_util import start_process_return_string


def binder_update_service() -> Tuple[int, str, str]:
    """binderを最新化する.

    $ wasanbon-admin.py binder update -v

    Returns:
       Tuple[int, str, str]: code, stdout, stderr
    """
    # オプションを指定して実行コマンドを生成する
    options = ["binder", "update", "-v"]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    return (code, stdout, stderr)


def binder_create_service(username: str, password: str, token: str) -> Tuple[int, str, str]:
    """binderを追加する.

    $ wasanbon-admin.py binder create -v -u username -p password -t token

    Returns:
       Tuple[int, str, str]: code, stdout, stderr
    """
    # オプションを指定して実行コマンドを生成する
    options = ["binder", "create", "-v", "-u", username, "-p", password, "-t", token]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    return (code, stdout, stderr)


def binder_commit_service(name: str, comment: str) -> Tuple[int, str, str]:
    """binderの変更をcommitする.

    $ wasanbon-admin.py binder commit <BINDER_OWNER_NAME> <COMMENT>

    Returns:
       Tuple[int, str, str]: code, stdout, stderr
    """
    # オプションを指定して実行コマンドを生成する
    options = ["binder", "commit", name, comment]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    return (code, stdout, stderr)


def binder_push_service(name: str, comment: str) -> Tuple[int, str, str]:
    """binderの変更をpushする.

    現状ではbinder pushコマンドがgithub認証方法の変更に対応してないためこの関数は未使用

    $ wasanbon-admin.py binder commit -p <BINDER_OWNER_NAME> <COMMENT>

    Returns:
       Tuple[int, str, str]: code, stdout, stderr
    """
    # オプションを指定して実行コマンドを生成する
    options = ["binder", "commit", "-p", name, comment]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    return (code, stdout, stderr)


def get_binder_list() -> Tuple[int, Optional[Dict[str, Dict[str, str]]], str]:
    """binderの一覧を確認する.

    $ wasanbon-admin.py binder list

    Returns:
       Tuple[int, Optional[Dict[str, Dict[str, str]]], str]: code, yaml_data, stderr
    """
    # オプションを指定して実行コマンドを生成する
    options = ["binder", "list"]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    yaml_data = None
    if code == 0:
        yaml_data = yaml.safe_load(stdout)

    return (code, yaml_data, stderr)


def get_binder_packages() -> Tuple[int, Optional[Dict[str, Dict[str, str]]], str]:
    """packageの一覧を確認する.

    $ wasanbon-admin.py binder packages -l

    Returns:
       Tuple[int, Optional[Dict[str, Dict[str, str]]], str]: code, yaml_data, stderr
    """
    # オプションを指定して実行コマンドを生成する
    options = ["binder", "packages", "-l"]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    yaml_data = None
    if code == 0:
        yaml_data = yaml.safe_load(stdout)

    return (code, yaml_data, stderr)


def get_binder_rtcs() -> Tuple[int, Optional[Dict[str, Dict[str, str]]], str]:
    """rtcの一覧を確認する.

    $ wasanbon-admin.py binder rtcs -l

    Returns:
       Tuple[int, Optional[Dict[str, Dict[str, str]]]: code, yaml_data, stderr
    """
    # オプションを指定して実行コマンドを生成する
    options = ["binder", "rtcs", "-l"]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    yaml_data = None
    if code == 0:
        yaml_data = yaml.safe_load(stdout)

    return (code, yaml_data, stderr)


def binder_add_package_service(ws: WS, binder_name: str, package_name: str) -> Tuple[int, str, str]:
    """binderにpackageを追加する.

    $ ./mgr.py binder add_package <BINDER_NAME>

    Returns:
       Tuple[int, str, str]: code, yaml_data, stderr
    """
    stdin_str = "1"
    # パッケージのディレクトリに移動する
    if ws == WS.dev:
        dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + package_name
    else:
        dir_path = EXECUTE_WORKSPACE_BASE_PATH + "/" + package_name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["binder", "add_package", binder_name]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command, stdin_str)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def binder_add_rtc_service(ws: WS, binder_name: str, package_name: str, rtc_name: str) -> Tuple[int, str, str]:
    """binderにrtcを追加する.

    $ ./mgr.py binder add_rtc <BINDER_NAME> <RTC_NAME>

    Returns:
       Tuple[int, str, str]: code, yaml_data, stderr
    """
    stdin_str = "1"
    # パッケージのディレクトリに移動する
    if ws == WS.dev:
        dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + package_name
    else:
        dir_path = EXECUTE_WORKSPACE_BASE_PATH + "/" + package_name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["binder", "add_rtc", binder_name, rtc_name]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command, stdin_str)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def update_package_in_binder_service(ws: WS, name: str, package_name: str) -> Tuple[int, str, str]:
    """ホストのbinder定義のコンポーネントを更新する.

    $ ./mgr.py binder update_package <BINDER_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(str): binder名
        package_name(str): パッケージ名

    Returns:
       Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = get_basepath(ws) + "/" + package_name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["binder", "update_package", name]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def update_rtc_in_binder_service(ws: WS, name: str, package_name: str, rtc_name: str) -> Tuple[int, str, str]:
    """ホストのbinder定義のコンポーネントを更新する.

    $ ./mgr.py binder update_rtc <BINDER_NAME> <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(str): binder名
        package_name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
       Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = get_basepath(ws) + "/" + package_name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["binder", "update_rtc", name, rtc_name]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def get_basepath(ws: WS) -> str:
    """wsに対応するパスを返却する.

    Args:
        ws(str): ワークスペース名

    Returns:
        str:実行パス
    """
    # パスの返却
    if ws == WS.dev:
        return DEVELOP_WORKSPACE_BASE_PATH
    elif ws == WS.exec:
        return EXECUTE_WORKSPACE_BASE_PATH

    return ""
