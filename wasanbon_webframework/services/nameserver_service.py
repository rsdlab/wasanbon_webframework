"""nameserverサービスモジュール."""
import logging
import sys
from typing import List, Tuple

from pexpect.exceptions import TIMEOUT
from pexpect.popen_spawn import PopenSpawn

import wasanbon_webframework.config.log_config  # noqa: F401

from .process_util import start_background_process_return_string, start_process_return_string
from .wasanbon_util import _generate_wasanbon_admin_command

logger = logging.getLogger(__name__)


def start_name_server(port: str) -> Tuple[int, str, str]:
    """wasanbon-admin.py nameserver startを実行する関数.

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    # すでにnameserverが起動していたらstartコマンドは実行しない
    # コマンドラインでrestartするか聞かれてしまうため
    code, _, _ = check_name_server(port)
    if code == 1:
        stdout = "nameserver is already started."
        return code, stdout, ""

    # オプションを指定して実行コマンドを生成する
    if port == "":
        wasanbon_command = _generate_nameserver_command(["start", "-v"])
    else:
        wasanbon_command = _generate_nameserver_command(["start", "-v", "-p", port])
    # macはnameserverが未起動でもパスワードを聞かれるので別処理にする
    if sys.platform == "darwin":
        # passwordは正しくなくても3回間違った後にnameserverを起動できる
        password = "temp_pass"
        wasanbon_command_str = "".join([cmd + " " for cmd in wasanbon_command])[:-1]
        code, stdout, stderr = _process_command_with_password(wasanbon_command_str, password)
        if code == 0 or code == 1:
            # タイムアウトしてもサーバ起動には通常成功している
            code, _, _ = check_name_server(port)
            if code == 1:
                stdout = "Starting Nameserver"
                return 0, stdout, ""
            else:
                stderr = "Failed to start nameserver."
                return -1, "", stderr
        return code, stdout, stderr
    else:
        code = start_background_process_return_string(wasanbon_command, True)
        return code, "Starting Nameserver", ""


def restart_name_server() -> Tuple[int, str, str]:
    """wasanbon-admin.py nameserver stopとstartを実行する関数.

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    # オプションを指定して実行コマンドを生成する
    wasanbon_command = _generate_nameserver_command(["restart", "-v"])
    # macだとパスワードを聞かれるので別処理にする
    if sys.platform != "darwin":
        # passwordは正しくなくても3回間違った後にnameserverを起動できる
        password = "temp_pass"
        wasanbon_command_str = "".join([cmd + " " for cmd in wasanbon_command])[:-1]
        code, stdout, stderr = _process_command_with_password(wasanbon_command_str, password)
        # restartの場合portが不明なのでcheck_runningできない
        return code, stdout, stderr
    else:
        code = start_background_process_return_string(wasanbon_command, True)
        return code, "Restarting Nameserver", ""


def stop_name_server() -> Tuple[int, str, str]:
    """wasanbon-admin.py nameserver stopを実行する関数.

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    # オプションを指定して実行コマンドを生成する
    code, stdout, stderr = start_process_return_string(_generate_nameserver_command(["stop", "-v"]))

    return code, stdout, stderr


def check_name_server(port: str) -> Tuple[int, str, str]:
    """wasanbon-admin.py nameserver check_runningを実行する関数.

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    # オプションを指定して実行コマンドを生成する
    if port == "":
        code, stdout, stderr = start_process_return_string(_generate_nameserver_command(["check_running", "-v"]))
    else:
        code, stdout, stderr = start_process_return_string(
            _generate_nameserver_command(["check_running", "-v", "-p", port])
        )

    return code, stdout, stderr


def _generate_nameserver_command(*args: List[str]) -> List[str]:
    """wasanbon-admin.py nameserver系のコマンドを生成する.

    Args:
        args(List[str]): wasanbon-admin.py nameserver 以降のコマンド

    Returns:
        List[str]: 実行結果
    """
    ret = ["nameserver"]
    ret.extend(*args)
    return _generate_wasanbon_admin_command(ret)


def _process_command_with_password(command: str, password: str) -> Tuple[int, str, str]:
    """パスワードが求められるコマンドを実行する.

    Args:
        command (str): コマンド
        password (str): パスワード

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    proc = PopenSpawn(command)
    stdout = ""
    stderr = ""
    additional_stdout = ""
    try:
        # password入力か、コマンド終了を待つ（たまにmacでもpasswordを聞かれないときがある
        while True:
            i = proc.expect(["[pP]assword*", "[#\$] "])  # noqa: W605
            if i == 0:
                proc.sendline(f"{password}\n")
                logger.info(f"stdout: {proc.before.decode()}")
                stdout += proc.before.decode()
            else:
                stdout += proc.before.decode()
                logger.info(f"stdout: {proc.before.decode()}")
                ret = proc.wait()
                logger.info(ret)
                break
    except TIMEOUT:
        ret = 1
        stderr = f"pexpect command({command}) is timedout"
        logger.info(stderr)
        additional_stdout = "Command is timed out. Please check if nameserver is running."
    except RuntimeError as e:
        ret = -1
        stderr = str(e)
        logger.warning(stderr)

    stdout = proc.before.decode() + additional_stdout

    return ret, stdout, stderr
