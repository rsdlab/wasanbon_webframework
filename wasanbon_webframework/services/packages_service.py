"""Git系のサービスモジュール."""
import logging
import os
import shutil
import stat
import traceback
from os import path
from typing import Any, Optional, Tuple

import yaml

from ..config.config import DEVELOP_WORKSPACE_BASE_PATH, EXECUTE_WORKSPACE_BASE_PATH, home_dir
from ..models.ws import WS
from ..services.wasanbon_util import _generate_mgr_command, _generate_wasanbon_admin_command
from .process_util import start_process_return_string

logger = logging.getLogger(__name__)


def get_packages_list(ws: WS) -> Tuple[int, Optional[Any], str]:
    """DWのパッケージの一覧を確認する.

    $ wasanbon-admin.py package list -l

    Args:
        ws(WS): ワークスペース名

    Returns:
        Dict: 実行結果{"text": output}
    """
    # オプションを指定して実行コマンドを生成する
    options = [
        "package",
        "list",
        "-l",
    ]
    print("yahho")
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)
    yaml_data = None
    if code == 0:
        if stdout:
            yaml_data = edit_stdout(stdout, ws)
        else:
            yaml_data = {}

    return (code, yaml_data, stderr)


def edit_stdout(stdout: str, ws: WS) -> Any:
    """パッケージの一覧の実行結果を指定されたwsでフィルタリングする.

    Args:
        stdout(str):実行結果
        ws(str): ワークスペース名

    Returns:
        str: 実行結果(yaml)
    """
    yaml_data = yaml.safe_load(stdout)
    basepath = get_basepath(ws)
    package_keys = [k for k, v in yaml_data.items()]
    for package_name in package_keys:
        # パスを取得
        packagepath = yaml_data[package_name]["path"]["root"]
        if basepath not in packagepath:
            # 対象外のパッケージを削除
            del yaml_data[package_name]

    return yaml_data


def get_rtcs_list(ws: WS, rtcs: str) -> Tuple[int, Optional[Any], str]:
    """DWのパッケージのコンポーネントの一覧を取得する.

    Args:
        ws(str): ワークスペース名
        rtcs:(str) パッケージ名

    Returns:
        Tuple[int, str, str]: return_code, yaml_data, stderr
    """
    # 実行パスを生成
    exec_path = os.path.join(get_basepath(ws), rtcs)
    # オプションを指定して実行コマンドを生成する
    options = [
        "rtc",
        "list",
        "-l",
    ]

    # カレントディレクトリをしてコマンドを実行する ※実行後、戻す
    command = _generate_mgr_command(exec_path, options)
    try:
        os.chdir(exec_path)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
        if not stdout:
            yaml_data = []
        else:
            yaml_data = yaml.safe_load(stdout)
    except FileNotFoundError:
        code = 1
        yaml_data = []
        stderr = traceback.format_exc()

    return (code, yaml_data, stderr)


def create_packages(ws: WS, name: str) -> Tuple[int, str, str]:
    """DWにパッケージを新規作成する.

    Args:
        ws(WS): ワークスペース名
        name:(str) パッケージ名

    Returns:
        int:結果コード
    """
    # 実行パスを生成
    exec_path = os.path.join(get_basepath(ws))
    # オプションを指定して実行コマンドを生成する
    options = [
        "package",
        "create",
        name,
        "-v",
    ]

    try:
        os.chdir(exec_path)
        command = _generate_wasanbon_admin_command(options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def delete_packages(name: str) -> Tuple[int, str, str]:
    """DWのパッケージを削除する.

    Args:
        name:(str) パッケージ名

    Returns:
        Tuple[int, str, str]: return_code, stdout, stderr
    """
    # オプションを指定して実行コマンドを生成する
    options = [
        "package",
        "delete",
        "-r",
        name,
        "-v",
    ]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    return (code, stdout, stderr)


def delete_rtc_package(ws: WS, name: str, rtc_name: str) -> Tuple[int, str, str]:
    """Delete RTC from Package.

    $ ./mgr.py rtc delete <RTC_NAME>

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Tuple[int, str, str]: return_code, stdout, stderr
    """
    # 実行パスを生成
    exec_path = os.path.join(get_basepath(ws), name)

    # オプションを指定して実行コマンドを生成する
    options = [
        "rtc",
        "delete",
        rtc_name,
        "-v",
    ]
    # カレントディレクトリをしてコマンドを実行する ※実行後、戻す
    try:
        os.chdir(exec_path)
        command = _generate_mgr_command(exec_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def git_clone_service(ws: WS, name: str) -> Tuple[int, str, str]:
    """gitからのcloneを行う.

    $ wasanbon-admin.py repository clone <PACKAGE_REPOSITORY_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH
    os.chdir(dir_path)

    options = ["repository", "clone", name, "-v"]
    command = _generate_wasanbon_admin_command(options)
    code, stdout, stderr = start_process_return_string(command)

    # 既に別ディレクトリでcloneされている場合、欠損のあるパッケージがcloneされるため、
    # cloneされたパッケージを削除する(エラーコード：4294967295)
    if code != 0:
        package_path = os.getcwd() + "/" + name
        file_path = package_path + "/mgr.py"
        if os.path.exists(package_path) and not os.path.isfile(file_path):
            try:
                for root, dirs, files in os.walk(package_path):
                    for dir in dirs:
                        os.chmod(path.join(root, dir), stat.S_IRWXU)
                    for file in files:
                        os.chmod(path.join(root, file), stat.S_IRWXU)
                shutil.rmtree(package_path)
                os.chdir(home_dir)
                logger.error("removed cloned packages " + name)
            except Exception as e:
                logger.error(e, exc_info=True)
                stderr = stderr + "\r\nremoved cloned packages " + name
                return (code, stdout, stderr)

    return (code, stdout, stderr)


def git_clone_rtc_service(ws: WS, name: str, rtc_name: str) -> Tuple[int, str, str]:
    """gitからのRTCのcloneを行う.

    $ ./mgr.py repository clone <REPO_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = os.path.join(get_basepath(ws), name)
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["repository", "clone", rtc_name, "-v"]
        command = _generate_mgr_command(dir_path, options)
        # 既にRTCがcloneされている場合、code=4294967295のERRORになる
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_init_service(ws: WS, name: str) -> Tuple[int, str, str]:
    """パッケージのgitリポジトリを初期化する.

    $ ./mgr.py admin git_init

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["admin", "git_init", "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_init_rtc_service(ws: WS, name: str, rtc_name: str) -> Tuple[int, str, str]:
    """gitローカルリポジトリを初期化する.

    $ ./mgr.py repository git_init <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["repository", "git_init", rtc_name, "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_commit_service(ws: WS, comment: str, name: str) -> Tuple[int, str, str]:
    """変更をローカルパッケージリポジトリにコミットする.

    $ ./mgr.py admin commit <COMMENT>

    Args:
        ws(WS): ワークスペース種別
        commit(str): コメント
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["admin", "commit", comment, "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_commit_rtc_service(ws: WS, comment: str, name: str, rtc_name: str) -> Tuple[int, str, str]:
    """変更をローカルパッケージリポジトリにコミットする.

    $ ./mgr.py repository clone <REPO_NAME>

    Args:
        ws(WS): ワークスペース種別
        comment(str): コメント
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["repository", "commit", rtc_name, comment, "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_push_service(ws: WS, name: str) -> Tuple[int, str, str]:
    """リポジトリをサーバーにpushする.

    $ ./mgr.py admin push

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["admin", "push", "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_push_rtc_service(ws: WS, name: str, rtc_name: str) -> Tuple[int, str, str]:
    """リポジトリをサーバーにpushする.

    $ ./mgr.py repository push <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["repository", "push", rtc_name, "-v"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_sync_rtc_service(ws: WS, name: str) -> Tuple[int, str, str]:
    """rtc/repository.yaml ファイルと各RTCリポジトリのバージョンハッシュを同期する.

    $ ./mgr.py repository sync

    Args:
        ws(WS): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = DEVELOP_WORKSPACE_BASE_PATH + "/" + name
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        options = ["repository", "sync"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_status_service(ws: WS, name: str) -> Tuple[int, str, str]:
    """パッケージのローカル リポジトリのステータスを表示する.

    $ ./mgr.py admin status

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
        options = ["admin", "status"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_rtc_status_service(ws: WS, name: str) -> Tuple[int, str, str]:
    """RTCのリポジトリステータスを表示する.

    $ ./mgr.py repository status

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
        options = ["repository", "status"]
        command = _generate_mgr_command(dir_path, options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_add_remote_service(ws: WS, url: str, name: str) -> Tuple[int, str, str]:
    """リモートリポジトリを追加する.

    $ git remote add origin <URL>

    Args:
        ws(str): ワークスペース種別
        url(str): URL
        name(str): パッケージ名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = os.path.join(get_basepath(ws), name)
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        command = ["git", "remote", "add", "origin", url]
        code, stdout, stderr = start_process_return_string(command)

        # リモート先が追加されたかをチェックする
        check_command = ["git", "remote", "-v"]
        check_code, stdout, check_stderr = start_process_return_string(check_command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def git_add_remote_rtc_service(ws: str, url: str, name: str, rtc_name: str) -> Tuple[int, str, str]:
    """リモートリポジトリを追加する.

    $ git remote add origin <URL>

    Args:
        ws(WS): ワークスペース種別
        url(str): URL
        name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Dict: 実行結果
    """
    # パッケージのディレクトリに移動する
    dir_path = f"{DEVELOP_WORKSPACE_BASE_PATH}/{name}/rtc/{rtc_name}"
    try:
        os.chdir(dir_path)
        # オプションを指定して実行コマンドを生成する
        command = ["git", "remote", "add", "origin", url]
        code, stdout, stderr = start_process_return_string(command)

        # リモート先が追加されたかをチェックする
        check_command = ["git", "remote", "-v"]
        check_code, stdout, check_stderr = start_process_return_string(check_command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    return (code, stdout, stderr)


def is_write_workspace(ws: WS) -> bool:
    """書き込みが許可されているワークスペースであるかチェックする.

    Args:
        ws(str): ワークスペース種別

    Returns:
        bool: 判定結果
    """
    if ws.value == WS.dev:
        return True
    else:
        return False


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
