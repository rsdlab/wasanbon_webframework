"""Deployのサービスモジュール."""
import logging
import os
import traceback
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import yaml
from fastapi import Request

import wasanbon_webframework.services.common_service as common_service
import wasanbon_webframework.services.packages_service as packages_service
from wasanbon_webframework.config.config import EXECUTE_WORKSPACE_BASE_PATH, home_dir
from wasanbon_webframework.services.wasanbon_util import _generate_mgr_command

from ..models.deploytarget import DeployTarget
from ..models.ws import WS
from ..services.wasanbon_util import _generate_command
from .process_util import start_process_return_string

logger = logging.getLogger(__name__)

PREFIX = "exec_"
SETTING_YAML = "setting.yaml"
REPO_YAML = "repository.yaml"


def deploy(ws: WS, deploy_target: DeployTarget, request: Request) -> Tuple[int, Optional[str], str]:
    """EWへのデプロイを行う.

    Args:
        ws(WS): ワークスペース種別
        deploy_target(DeployTarget): DeployTargetクラス
        request(Request):Requestクラス

    Returns:
        Tuple[int, Optional[str], str]:code, stdout, stderr
    """
    # 各値を設定
    rts_git_url = deploy_target.rts_git_url
    hash = deploy_target.commit_hash
    url = urlparse(str(request.url))
    ip = url.netloc.split(":")

    # URLからパッケージ名を取得する
    pkg_name = get_package_dir(rts_git_url)
    if pkg_name == "":
        stderr = "Could not get package name from URL"
        return (1, "", stderr)

    # EW登録パッケージをチェックし、削除を行う
    code, stdout, stderr = del_exec_package(ws)
    if code != 0:
        return code, stdout, stderr

    # EWにパッケージ作成
    code, stdout, stderr = create_package(pkg_name)
    if code != 0:
        return code, stdout, stderr

    # Gitリポジトリ新規作成
    code, stdout, stderr = git_init(pkg_name)
    if code != 0:
        return code, stdout, stderr

    # リモートリポジトリ追加
    code, stdout, stderr = git_remote_add(pkg_name, rts_git_url)
    if code != 0:
        return code, stdout, stderr

    # ローカルリポジトリへ反映
    code, stdout, stderr = git_fetch(pkg_name)
    if code != 0:
        return code, stdout, stderr

    # チェックアウト
    code, stdout, stderr = git_checkout_hash(pkg_name, hash)
    if code != 0:
        return code, stdout, stderr

    # setting.yamlの編集
    code, stdout, stderr = edit_setting_yaml(pkg_name)
    if code != 0:
        return code, stdout, stderr

    # RTC一覧の取得
    clone_list, error_list = get_rtc_list(pkg_name, ip[0])
    # DefaultSystem.xmlからpathUriを取得できなかった場合
    if len(error_list) > 0:
        code = 1
        stderr = error_list[0]
        return code, stdout, stderr

    # RTCのclone
    code, stdout, stderr = rtc_clone(clone_list, pkg_name)
    if code == 0:
        stdout = f"Deployment to Execute workspace completed. Cloned RTCs: {clone_list}"

    return (code, stdout, stderr)


def del_exec_package(ws: WS) -> Tuple[int, Optional[str], str]:
    """EWに登録されているパッケージを削除する.

    Args:
        ws(WS): ワークスペース種別

    Returns:
        Tuple[int,  Optional[str], str]:code, stdout, stderr
    """
    # EWに登録されているパッケージをチェックし、登録されていれば削除する
    code, stdout, stderr = packages_service.get_packages_list(ws)
    if code == 0 and stdout is not None:
        if len(stdout) != 0:
            # パッケージ情報が取得できた場合、keyを取得する
            package_keys = [k for k, v in stdout.items()]
            # EWのパッケージを削除する(基本は1つのみ存在する)
            for package_name in package_keys:
                logger.info(f"Remove registered packages ({package_name})")
                code, stdout, stderr = packages_service.delete_packages(package_name)

    return (code, stdout, stderr)


def create_package(pkg_name: str) -> Tuple[int, str, str]:
    """EWにパッケージ作成を行う.

    Args:
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    code, stdout, stderr = packages_service.create_packages(WS.exec, PREFIX + pkg_name)
    return (code, stdout, stderr)


def git_init(pkg_name: str) -> Tuple[int, str, str]:
    """リポジトリの新規作成をする.

    $ git init

    Args:
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    exec_path = os.path.join(common_service.get_basepath(WS.exec), PREFIX + pkg_name)
    options = [
        "git",
        "init",
    ]
    code, stdout, stderr = exec_command(exec_path, options)
    return (code, stdout, stderr)


def git_remote_add(pkg_name: str, url: str) -> Tuple[int, str, str]:
    """リモートリポジトリを追加する.

    $ git remote add origin <URL>

    Args:
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    code, stdout, stderr = packages_service.git_add_remote_service(WS.exec, url, PREFIX + pkg_name)
    return (code, stdout, stderr)


def git_fetch(pkg_name: str) -> Tuple[int, str, str]:
    """リモートリポジトリの最新をローカルリポジトリへと反映する.

    $ git fetch -a

    Args:
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    exec_path = os.path.join(common_service.get_basepath(WS.exec), PREFIX + pkg_name)
    options = [
        "git",
        "fetch",
        "-a",
    ]
    code, stdout, stderr = exec_command(exec_path, options)
    return (code, stdout, stderr)


def git_checkout_hash(pkg_name: str, hash: str) -> Tuple[int, str, str]:
    """指定されたコミットハッシュへcheckoutを行う リモートリポジトリを正として、ローカルリポジトリへ強制上書きする.

    $ git checkout -f <HASH>

    Args:
        pkg_name(str): パッケージ名
        hash(str):ハッシュ値

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    exec_path = os.path.join(common_service.get_basepath(WS.exec), PREFIX + pkg_name)
    options = [
        "git",
        "checkout",
        "-f",
        hash,
    ]
    code, stdout, stderr = exec_command(exec_path, options)
    return (code, stdout, stderr)


def edit_setting_yaml(pkg_name: str) -> Tuple[int, str, str]:
    """Yamlファイルのパッケージ名(name)の編集を行う.

    Args:
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    rename_pkg_name = PREFIX + pkg_name
    exec_path = os.path.join(common_service.get_basepath(WS.exec), rename_pkg_name)
    try:
        # git pullでsetting.yamlを上書きしたため編集を行う
        os.chdir(exec_path)
        with open(SETTING_YAML) as in_file:
            yaml_data = yaml.safe_load(in_file)
        # 「name」を編集する
        yaml_data["application"]["name"] = rename_pkg_name
        # 上書きして出力
        with open(SETTING_YAML, "w") as out_file:
            yaml.dump(yaml_data, out_file, allow_unicode=True, default_flow_style=False, sort_keys=False)
        os.chdir(home_dir)
        code = 0
        stderr = ""
    except (FileNotFoundError, yaml.YAMLError):
        code = 1
        stderr = traceback.format_exc()

    return (code, "", stderr)


def get_rtc_list(pkg_name: str, ip: str) -> Tuple[List[str], List[str]]:
    """DefaultSystem.xmlからcloneするRTCの一覧を作成する.

    Args:
        pkg_name(str): パッケージ名
        ip(str):IPアドレス

    Returns:
        clone_rtc_list: cloneするRTCリスト
    """
    rename_pkg_name = PREFIX + pkg_name
    rtc_list, error_list = common_service.get_rts_host(WS.exec, rename_pkg_name)

    # ホスト名設定
    hostname = "localhost"
    clone_rtc_list = []
    for rtc in rtc_list:
        if hostname in rtc or ip in rtc:
            start_str = rtc.rfind("/")
            end_str = rtc.find(".rtc")
            if start_str > 0 and end_str > 0:
                rtc_name = rtc[start_str + 1 : end_str - 1]
                clone_rtc_list.append(rtc_name)

    return clone_rtc_list, error_list


def rtc_clone(clone_list: List[str], pkg_name: str) -> Tuple[int, str, str]:
    """RTCのcloneを行う.

    Args:
        clone_list(List[str]): RTCリスト
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    code = 0
    stdout = ""
    stderr = ""
    exec_path = os.path.join(common_service.get_basepath(WS.exec), PREFIX + pkg_name)
    error_rtc = []
    try:
        os.chdir(exec_path)
        git_rtc_list: Dict[str, str] = {}
        for rtc_name in clone_list:
            git_url, git_hush = get_rtc_git(PREFIX + pkg_name, rtc_name)
            git_rtc_list[rtc_name] = git_hush
            code, stdout, stderr = start_process_return_string(
                _generate_mgr_command(exec_path, ["repository", "clone", "-u", git_url, "-v"])
            )
            if code != 0:
                error_rtc.append(f"{rtc_name} failed to clone ({stderr})")
                continue
            cloned_dir_name = get_package_dir(git_url)
            os.rename(os.path.join("rtc", cloned_dir_name), os.path.join("rtc", rtc_name))
        for rtc_name in clone_list:
            hash_code, hash_stdout, hash_stderr = git_rtc_checkout_hash(
                PREFIX + pkg_name, rtc_name, git_rtc_list[rtc_name]
            )
            if hash_code != 0:
                error_rtc.append(f"{rtc_name} failed to checkout ({hash_stderr})")
    except Exception:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    if len(error_rtc) != 0:
        code = 2
        stdout = ""
        stderr = str(error_rtc)
    os.chdir(home_dir)
    return (code, stdout, stderr)


def exec_command(exec_path: str, options: List[str]) -> Tuple[int, str, str]:
    """指定されたコマンドを実行する(共通処理).

    Args:
        exec_path(str): 実行パス
        options(List[str]): コマンドオプション

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    try:
        os.chdir(exec_path)
        command = _generate_command(options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    if code == 0:
        logger.info(stdout)
    else:
        logger.error(stderr)
    return (code, stdout, stderr)


def get_package_dir(url: str) -> str:
    """URLからパッケージ名を取得する.

    Args:
        url(str): URL

    Returns:
        str: パッケージ名
    """
    start_str = url.rfind("/")
    end_str = url.find(".git")

    if start_str < 0 or end_str < 0:
        pkg_name = ""
    else:
        pkg_name = url[start_str + 1 : end_str]

    return pkg_name


def get_rtc_git(package_name: str, rtc_name: str) -> Tuple[str, str]:
    """RTC名からgit URLとhashを取得する.

    Args:
        package_name(str): パッケージ名
        rtc_name(str): RTC名

    Returns:
        Tuple[str, str]: git URL, hash
    """
    file_path = os.path.normpath(f"{EXECUTE_WORKSPACE_BASE_PATH}/{package_name}/rtc/repository.yaml")
    # repository.yml、DefaultSystem.xml双方のRTC名を小文字で統一する
    with open(file_path, "r") as yml:
        _yml_data = yaml.safe_load(yml)
        yml_data = {}
        for k, v in _yml_data.items():
            yml_data[k.lower()] = v
    git_url = yml_data[rtc_name.lower()]["git"]
    git_hash = yml_data[rtc_name.lower()]["hash"]
    return (git_url, git_hash)


def git_rtc_checkout_hash(package_name: str, rtc_name: str, hash: str) -> Tuple[int, str, str]:
    """指定されたコミットハッシュへcheckoutを行う.

    $ git checkout -f <HASH>

    Args:
        package_name(str): パッケージ名
        rtc_name(str): RTC名
        hash(str):ハッシュ値

    Returns:
        Tuple[int, str, str]:code, stdout, stderr
    """
    file_path = os.path.join(EXECUTE_WORKSPACE_BASE_PATH, package_name, "rtc", rtc_name)
    os.chdir(file_path)
    options = [
        "git",
        "checkout",
        "-f",
        hash,
    ]
    code, stdout, stderr = start_process_return_string(options)
    return (code, stdout, stderr)
