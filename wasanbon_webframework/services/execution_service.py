"""RTShell系のサービスモジュール."""

import logging
import os
import shlex
import traceback
from typing import List, Optional, Tuple
import subprocess
import re
import time
import signal
from pathlib import Path

import psutil
import yaml
from fastapi import Request

import wasanbon_webframework.services.common_service as common_service
from wasanbon_webframework.models.rtcname import RtcName

from ..config.config import (
    DEVELOP_WORKSPACE_BASE_PATH,
    EXECUTE_WORKSPACE_BASE_PATH,
    WW_BASE_PATH,
    home_dir,
)
from ..models.ws import WS
from ..services.wasanbon_util import _generate_command, _generate_mgr_command
from .process_util import start_background_process_return_string, start_process_return_string

logger = logging.getLogger(__name__)

def run_module(ws: WS, pkg_name: str, module_name: str) -> Tuple[int, str, str]:
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    is_rtc = is_rtc_installed(exec_path)
    stdout = ""
    stderr = ""
    # if is_rtc:
    options = [
        "module",
        "run",
        module_name,
        "-b",
    ]
    try:
        os.chdir(exec_path)
        mgr_command = _generate_mgr_command(exec_path, options)
        mgr_command_str = " ".join(shlex.quote(arg) for arg in mgr_command)
        command = ["bash", "-ic", f"source ~/.bashrc; {mgr_command_str}"]
        code = start_background_process_return_string(command, True)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stderr = traceback.format_exc()

    # else:
    #     code = 255
    #     stderr = f"RTC not installed in Package ({pkg_name})"

    return (code, stdout, stderr)

##ROS1用
# def roscore_run() -> Tuple[int, str, str]:

#     def _run(cmd: List[str]) -> subprocess.CompletedProcess:
#         return subprocess.run(cmd, capture_output=True, text=True)

#     def _find_rosmaster_pid_via_ps() -> List[int]:
#         pids = set()
#         try:
#             res = _run(["ps", "-ef"])
#             for line in res.stdout.splitlines():
#                 if "/opt/ros/noetic/bin/rosmaster" not in line:
#                     continue
#                 if "grep" in line:
#                     continue
#                 cols = line.split()
#                 if len(cols) >= 2 and cols[1].isdigit():
#                     pids.add(int(cols[1]))
#         except Exception:
#             pass
#         return sorted(pids)

#     def _pid_alive(pid: int) -> bool:
#         if pid <= 1:
#             return False
#         try:
#             os.kill(pid, 0)
#             return True
#         except ProcessLookupError:
#             return False
#         except PermissionError:
#             return True

#     def _kill_pids(pids: List[int], grace_sec: float = 1.5) -> None:
#         if not pids:
#             return
#         me = os.getpid()
#         for pid in pids:
#             if pid == me:
#                 continue
#             try:
#                 os.kill(pid, signal.SIGTERM)
#             except ProcessLookupError:
#                 pass
#             except Exception:
#                 pass
#         time.sleep(grace_sec)
#         still = [pid for pid in pids if pid != me and _pid_alive(pid)]
#         for pid in still:
#             try:
#                 os.kill(pid, signal.SIGKILL)
#             except ProcessLookupError:
#                 pass
#             except Exception:
#                 pass

#     def stop_existing_master() -> List[int]:
#         pids = _find_rosmaster_pid_via_ps()
#         if pids:
#             _kill_pids(pids)
#             time.sleep(0.8)
#         return pids

#     def start_roscore_detached(port: str, log_path: Path) -> Optional[int]:
#         try:
#             log_path.parent.mkdir(parents=True, exist_ok=True)
#             logf = open(log_path, "ab", buffering=0)
#         except Exception:
#             # ログが開けない場合でも起動は試す
#             logf = subprocess.DEVNULL
#         try:
#             proc = subprocess.Popen(
#                 ["bash", "-ic", f"source ~/.bashrc; roscore -p {shlex.quote(str(port))}"],
#                 stdout=logf,
#                 stderr=logf,
#                 start_new_session=True,
#                 close_fds=True,
#                 env=os.environ.copy(),
#             )
#             return proc.pid
#         except FileNotFoundError:
#             return None

#     def wait_for_rosout(timeout_sec: float) -> Tuple[bool, str, str]:
#         start = time.time()
#         last_out, last_err = "", ""
#         while time.time() - start < timeout_sec:
#             try:
#                 rtn = subprocess.run(
#                     ["bash", "-ic", "source ~/.bashrc; rosnode list"],
#                     capture_output=True,
#                     text=True,
#                 )
#                 last_out, last_err = rtn.stdout, rtn.stderr
#                 if "/rosout" in last_out.splitlines():
#                     return True, last_out, ""
#             except Exception as e:
#                 last_err = str(e)
#             time.sleep(0.8)
#         return False, last_out, last_err

#     # Main flow
#     port = os.environ.get("ROSCORE_PORT", "11311")
#     log_dir = Path.home() / ".ros" / "autostart"
#     log_file = log_dir / "roscore.log"

#     stopped = stop_existing_master()

#     pid = start_roscore_detached(port, log_file)
#     if not pid:
#         return (1, "", "Failed to start roscore. 'roscore' not found or could not spawn.")

#     ok, verify_out, verify_err = wait_for_rosout(timeout_sec=12.0)
#     if ok:
#         msg = f"roscore started (PID={pid}) on port {port}. Log: {str(log_file)}. /rosout is up."
#         if stopped:
#             msg = f"Stopped existing ({stopped}). " + msg
#         return (0, msg, "")
#     else:
#         err = "Timeout waiting for /rosout."
#         if verify_err:
#             err += f" Detail: {verify_err}"
#         return (1, verify_out, err)


def middleware_check(ws: WS, pkg_name: str) -> Tuple[int, str, str]:
    """Run './mgr.py module middleware' in the specified package."""
    options = [
        "module",
        "middleware",
    ]
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    command = _generate_mgr_command(exec_path, options)
    cwd = os.getcwd()
    try:
        os.chdir(exec_path)
        code, stdout, stderr = start_process_return_string(command)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()
    finally:
        os.chdir(cwd)

    return (code, stdout.strip(), stderr)

def set_server_plus_ros2(
    ws: WS,
    pkg_name: str,
    server_ip: str,
    local_ip: str,
    domain_id: int,
    system_name: str,
) -> Tuple[int, str, str]:
    
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    options = [
        "server",
        "set",
        server_ip,
        local_ip,
        str(domain_id),
        system_name,
    ]
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

def set_server_ros2(
    ws: WS,
    pkg_name: str,
    server_ip: str,
    local_ip: str,
    domain_id: int,
) -> Tuple[int, str, str]:
    
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    options = [
        "server",
        "set",
        server_ip,
        local_ip,
        str(domain_id),
    ]
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


def set_ros2_network_settings(
    domain_id: int,
    bashrc_path: str = os.path.expanduser("~/.bashrc"),
) -> bool:

    try:
        domain_id = int(domain_id)
        if not 0 <= domain_id <= 232:
            logger.error("ROS_DOMAIN_ID must be between 0 and 232.")
            return False
        if not os.path.exists(bashrc_path):
            Path(bashrc_path).touch()

        with open(bashrc_path, "r", encoding="utf-8") as bashrc:
            lines = bashrc.readlines()

        updated_lines = []

        for line in lines:
            if "ROS_DOMAIN_ID" in line:
                if line.lstrip().startswith("#"):
                    updated_lines.append(line)
                else:
                    newline = "\n" if not line.endswith("\n") else ""
                    updated_lines.append("# " + line + newline)
            else:
                updated_lines.append(line)

        if updated_lines and not updated_lines[-1].endswith("\n"):
            updated_lines[-1] += "\n"

        updated_lines.append(
            f"\nexport ROS_DOMAIN_ID={domain_id}\n"
        )

        with open(bashrc_path, "w", encoding="utf-8") as bashrc:
            bashrc.writelines(updated_lines)
        os.environ["ROS_DOMAIN_ID"] = str(domain_id)
        logger.info(
            "ROS2 network setting updated: ROS_DOMAIN_ID=%s",
            domain_id,
        )
        return True

    except Exception as error:
        logger.error(
            "Failed to update ROS2 network setting: %s",
            error,
        )
        return False

def check_ros2_network_settings(
    domain_id: int,
    bashrc_path: str = os.path.expanduser("~/.bashrc"),
) -> bool:
    try:
        expected_domain_id = str(domain_id)
        # 現在の環境変数を確認
        current_domain_id = os.environ.get("ROS_DOMAIN_ID")
        if current_domain_id == expected_domain_id:
            return True

        # 環境変数に反映されていない場合は .bashrc を確認
        if not os.path.exists(bashrc_path):
            return False

        with open(bashrc_path, "r", encoding="utf-8") as bashrc:
            lines = bashrc.readlines()
        # 後ろから見て、最後の有効なROS_DOMAIN_IDを確認
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("#"):
                continue
            match = re.match(
                r"^export\s+ROS_DOMAIN_ID=(\d+)$",
                line,
            )
            if match:
                return match.group(1) == expected_domain_id
        return False

    except Exception as error:
        logger.error(
            "Error checking ROS2 network setting: %s",
            error,
        )
        return False

def run_system_ex(ws: WS, pkg_name: str, system_name: str) -> Tuple[int, str, str]:

    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    is_rtc = is_rtc_installed(exec_path)
    stdout = ""
    stderr = ""
    if is_rtc:
        options = [
            "system",
            "run",
            system_name,
            "-b",
        ]
        try:
            command = _generate_mgr_command(exec_path, options)
            command_str = " ".join(shlex.quote(arg) for arg in command)
            os.chdir(exec_path)
            code = start_background_process_return_string(
                ["bash", "-ic", f"source ~/.bashrc; {command_str}"], True
            )
            os.chdir(home_dir)
        except FileNotFoundError:
            code = 1
            stderr = traceback.format_exc()
    else:
        options = [
            "system",
            "run",
            system_name,
            "-b",
        ]
        try:
            os.chdir(exec_path)
            command = _generate_mgr_command(exec_path, options)
            command_str = " ".join(shlex.quote(arg) for arg in command)
            code = start_background_process_return_string(
                ["bash", "-ic", f"source ~/.bashrc; {command_str}"], True
            )
            os.chdir(home_dir)

        except FileNotFoundError:
            code = 1
            stderr = traceback.format_exc()

    # else:
    #     code = 255
    #     stderr = f"RTC not installed in Package ({pkg_name})"

    return (code, stdout, stderr)

##ROS1用
# def get_ros_master_uri() -> str:
#     candidates = [os.path.expanduser("~/.rosrc"), os.path.expanduser("~/.bashrc")]

#     for path in candidates:
#         if not os.path.exists(path):
#             continue

#         with open(path, "r") as f:
#             lines = f.readlines()

#         for line in reversed(lines): 
#             line = line.strip()
#             if line.startswith("#") or "ROS_MASTER_URI" not in line:
#                 continue

#             match = re.match(r'^export\s+ROS_MASTER_URI=(["\']?)(http://[^"\']+)\1', line)
#             if match:
#                 return match.group(2)

#     # 見つからなかった場合のデフォルト
#     return "http://localhost:11311"


# def set_ros_network_settings(
#     server_ip: str,
#     request: Request,
#     bashrc_path: str = os.path.expanduser("~/.bashrc"),
# ) -> bool:
#     """Update ROS networking environment variables in ~/.bashrc using request info."""

#     try:
#         host_header = request.headers.get("host")
#         client_ip = host_header.split(":", 1)[0] if host_header else None
#         if not client_ip:
#             client_ip = request.url.hostname
#         if not client_ip:
#             client_ip = request.client.host
#         if not client_ip:
#             logger.error("Could not determine server IP from request for ROS setup.")
#             return False
#         ros_master = f"export ROS_MASTER_URI=http://{server_ip}:11311"
#         ros_ip = f"export ROS_IP={client_ip}"

#         with open(bashrc_path, "r", encoding="utf-8") as bashrc:
#             lines = bashrc.readlines()

#         updated_lines = []
#         for line in lines:
#             if any(key in line for key in ["ROS_MASTER_URI", "ROS_IP", "ROS_HOSTNAME"]):
#                 if line.lstrip().startswith("#"):
#                     updated_lines.append(line)
#                 else:
#                     newline = "\n" if not line.endswith("\n") else ""
#                     updated_lines.append("# " + line + newline if not line.startswith("#") else line)
#             else:
#                 updated_lines.append(line)

#         if updated_lines and not updated_lines[-1].endswith("\n"):
#             updated_lines[-1] = updated_lines[-1] + "\n"

#         updated_lines.append("\n" + ros_master + "\n")
#         updated_lines.append(ros_ip + "\n")

#         with open(bashrc_path, "w", encoding="utf-8") as bashrc:
#             bashrc.writelines(updated_lines)

#         os.environ["ROS_MASTER_URI"] = f"http://{server_ip}:11311"
#         os.environ["ROS_IP"] = client_ip

#         logger.info("ROS network settings updated: ROS_MASTER_URI=%s, ROS_IP=%s", server_ip, client_ip)
#         return True
#     except Exception as error:
#         logger.error("Failed to update ROS network settings: %s", error)
#         return False


# def check_ros_network_settings(server_ip: str, request: Request) -> bool:
#     try:
#         ros_ip = os.environ.get("ROS_IP")
#         ros_master_uri = os.environ.get("ROS_MASTER_URI")
#         request_host = request.client.host

#         is_ros_ip_ok = ros_ip == request_host
#         is_master_uri_ok = ros_master_uri and server_ip in ros_master_uri

#         return is_ros_ip_ok and is_master_uri_ok
#     except Exception as e:
#         logger.error(f"Error checking ROS network settings: {e}")
#         return False

# def find_dir_in_src(target_dir_name, src_root="/home/rsdlab/test_fw/src"):
#     for root, dirs, files in os.walk(src_root):
#         if os.path.basename(root) == target_dir_name:
#             parent_path = os.path.dirname(root)
#             return os.path.abspath(parent_path)
#     return None
####ここまで

def start_system(ws: WS, pkg_name: str, rtc_name: Optional[RtcName]) -> Tuple[int, str, str]:
    """Start system without activation (bellow command) or execute an RTC if spacified.

    $ ./mgr.py system run -f <system.xml> -p -b or ./mgr.py rtc run <RTC_NAME>

    Args:
        ws(WS): ワークスペース種別
        pkg_name(str): パッケージ名
        rtc_name(RtcName): RTC名

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    # 実行パスを生成
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    if rtc_name is not None:
        if len(rtc_name.rtc_name) == 0:
            # RTCの指定がない場合、システムを起動する
            code, stdout, stderr = start_run_system(exec_path, pkg_name)
        else:
            # RTCの指定がある場合、RTCを起動する
            code, stdout, stderr = start_run_rtc(exec_path, rtc_name.rtc_name)
    else:
        # RTCの指定がない場合、システムを起動する
        code, stdout, stderr = start_run_system(exec_path, pkg_name)

    return (code, stdout, stderr)


def start_run_system(path: str, pkg_name: str) -> Tuple[int, str, str]:
    """Start system without activation (bellow command).

    $ ./mgr.py system run -f <system.xml> -p -b

    Args:
        path(str): 実行パス
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    stdout = ""
    stderr = ""
    options = [
        "system",
        "run",
        "-f",
        "DefaultSystem.xml",
        "-p",
        "-b",
    ]
    try:
        os.chdir(path)
        command = _generate_mgr_command(path, options)
        code = start_background_process_return_string(command, True)
        os.chdir(home_dir)
        stdout = f"System Started ({pkg_name})"
    except FileNotFoundError:
        code = 255
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def start_run_rtc(path: str, rtc_name: str) -> Tuple[int, str, str]:
    """Execute an RTC if spacified.

    $ ./mgr.py rtc run <RTC_NAME>

    Args:
        path(str): 実行パス
        rtc_name(str): RTC名

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    stdout = ""
    stderr = ""
    # パッケージ内に指定されたRTCがあることをチェックする
    rtc_flg = is_rtc(path, rtc_name)
    if rtc_flg:
        # OKの場合、プロセスの存在チェック
        process_flg = is_process(rtc_name)
        if process_flg:
            code = 1
            stderr = f"RTC Process Already Started ({rtc_name})"
        else:
            # 対象RTCを起動する
            options = [
                "rtc",
                "run",
                rtc_name,
            ]
            # カレントディレクトリを実行時にのみ変更する
            # ※ try-exceptはRTCのチェック時に行っているため、ここでは割愛する
            os.chdir(path)
            command = _generate_mgr_command(path, options)
            code = start_background_process_return_string(command)
            os.chdir(home_dir)
            # バックグラウンド実行だと、Noneとなるため0を設定して返却する
            if code is None:
                code = 0
                stdout = f"RTC Started ({rtc_name})"
    else:
        # NGの場合
        code = 255
        stderr = f"RTC is not installed ({rtc_name})"

    return (code, stdout, stderr)


def run_system(ws: WS, pkg_name: str) -> Tuple[int, str, str]:
    """Launch System.

    $ ./mgr.py system run -v -b

    Args:
        ws(WS): ワークスペース種別
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    # 実行パスを生成
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    # RTCがインストールされているかチェックする。RTCが何もないとコマンドが失敗する。
    is_rtc = is_rtc_installed(exec_path)
    stdout = ""
    stderr = ""
    if is_rtc:
        options = [
            "system",
            "run",
            "-v",
            "-b",
        ]
        try:
            # カレントディレクトリを実行時にのみ変更する
            os.chdir(exec_path)
            command = _generate_mgr_command(exec_path, options)
            code = start_background_process_return_string(command, True)
            os.chdir(home_dir)
        except FileNotFoundError:
            code = 1
            stderr = traceback.format_exc()

    else:
        code = 255
        stderr = f"RTC not installed in Package ({pkg_name})"

    return (code, stdout, stderr)


def activate_rtcs(ws: WS, pkg_name: str) -> Tuple[int, str, str]:
    """Activate RTCs.

    rtstart system.xml -v

    Args:
        ws(WS): ワークスペース種別
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr

    """
    # 実行パスを生成
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    options = [
        "rtstart",
        "system/DefaultSystem.xml",
        "-v",
    ]
    try:
        os.chdir(exec_path)
        command = _generate_command(options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def deactivate_rtcs(ws: WS, pkg_name: str) -> Tuple[int, str, str]:
    """Deactivate RTCs.

    rtstop system.xml -v

    Args:
        ws(WS): ワークスペース種別
        name(PackageName): パッケージ名

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr

    """
    # 実行パスを生成
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    options = [
        "rtstop",
        "system/DefaultSystem.xml",
        "-v",
    ]
    try:
        os.chdir(exec_path)
        command = _generate_command(options)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def is_rtc(path: str, rtc_name: str) -> bool:
    """repositoryに存在しているRTCパッケージであるかチェックする.

    Args:
        path(str): 実行パス

    Returns:
        bool:判定結果(True:該当パッケージあり,False:該当パッケージなし)
    """
    options = [
        "repository",
        "list",
    ]
    command = _generate_mgr_command(path, options)
    # カレントディレクトリを実行時にのみ変更する
    try:
        os.chdir(path)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        logger.error(traceback.format_exc())
        return False

    if code != 0:
        return False
    else:
        yaml_data = yaml.safe_load(stdout)
        rtc_list = [k for k in yaml_data]
        return rtc_name in rtc_list


def is_rtc_installed(path: str) -> bool:
    """指定された実行パス(パッケージに)にRTCがインストールされているかチェックする.

    Args:
        path(str): 実行パス

    Returns:
        bool:判定結果(True:インストールあり,False:インストールなし)
    """
    options = [
        "rtc",
        "list",
    ]
    command = _generate_mgr_command(path, options)
    # カレントディレクトリを実行時にのみ変更する
    try:
        os.chdir(path)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        logger.error(traceback.format_exc())
        return False

    # 結果が取得できない場合、RTCが何もインストールされていない
    if code == 0:
        if len(stdout) != 0:
            return True
        else:
            return False
    else:
        return False


def rtresurrect_connections(ws: WS, pkg_name: str) -> Tuple[int, str, str]:
    """RTCのポートを接続する.

    rtresurrect system.xml -v

    Args:
        ws(str): ワークスペース種別
        name(str): パッケージ名

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    # 実行パスを生成
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    options = [
        "rtresurrect",
        "system/DefaultSystem.xml",
        "-v",
    ]
    command = _generate_command(options)
    # カレントディレクトリを実行時にのみ変更する
    try:
        os.chdir(exec_path)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def disconnect_connections(ws: WS, pkg_name: str) -> Tuple[int, str, str]:
    """RTCのポートを切断する.

    rtteardown system.xml -v

    Args:
        ws(WS): ワークスペース種別
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr
    """
    # 実行パスを生成
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    options = [
        "rtteardown",
        "system/DefaultSystem.xml",
        "-v",
    ]
    command = _generate_command(options)
    # カレントディレクトリを実行時にのみ変更する
    try:
        os.chdir(exec_path)
        code, stdout, stderr = start_process_return_string(command)
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stdout = ""
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def rtc_status(ws: WS, pkg_name: str) -> Tuple[int, List[str], List[str]]:
    """RTCの死活状況、ポート接続状態を取得する.

    $ rtcat -l <RTC_FULL_PATH> -v

    Args:
        ws(str): ワークスペース種別
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, List[str], List[str]]: return_code, out_list, err_list
    """
    rtc_list, error_list = get_rtc_list(ws, pkg_name)
    code = 0
    out_list = []
    err_list = []
    if len(error_list) > 0:
        code = 1
        err_list = error_list
    else:
        is_error = False
        for rtc_full_path in rtc_list:
            options = [
                "rtcat",
                "-l",
                rtc_full_path,
                "-v",
            ]
            command = _generate_command(options)
            code, stdout, stderr = start_process_return_string(command)
            if code == 0 and stdout:
                out_list.append(stdout)
            else:
                if not is_error:
                    is_error = True
                err_list.append(stderr)

        # エラーが発生していたら終了コードを「1」に設定する
        if is_error:
            code = 1
    return (code, out_list, err_list)


def exit_rtc(rtc_list: List[str]) -> Tuple[int, str, str]:
    """Exit RTCs.

    rtexit <RTC_FULL_PATH> -v

    Args:
        rtc_list(list[str]): RTCリスト

    Returns:
        Tuple[int, str, str]: return_code, strdout, stderr

    """
    code = 0
    stdout = ""
    stderr = ""
    for rtc_full_path in rtc_list:
        options = [
            "rtexit",
            rtc_full_path,
            "-v",
        ]
        # コマンドの実行結果はコードのみ
        command = _generate_command(options)
        code, stdout, stderr = start_process_return_string(command)
        if code != 0:
            # エラーが発生した時点で終了する
            return (code, stdout, stderr)

    return (code, stdout, stderr)


def del_rtc(rtc_list: List[str]) -> Tuple[int, str, List[str]]:
    """Del RTCs.

    rtdel <RTC_FULL_PATH> -v

    Args:
        rtc_list(list[str]): RTCリスト

    Returns:
        Tuple[int, str, List[str]]: return_code, strdout, err_list

    """
    stdout = ""
    err_list = []
    for rtc_full_path in rtc_list:
        options = [
            "rtdel",
            rtc_full_path,
            "-v",
        ]
        command = _generate_command(options)
        code, stdout, stderr = start_process_return_string(command)
        if code != 0:
            err_list.append(stderr)

    # rtdelは失敗しても正常とみなす
    return (0, stdout, err_list)


def terminate_system(ws: WS, pkg_name: str, rtc_name: Optional[RtcName]) -> Tuple[int, str, str]:
    """Terminate Launched System(bellow command) or teminate an RTC if spacified.

    Args:
        pkg_name:パッケージ名
        rtc_name:RTC名

    Returns:
        Tuple[int, str, str]: code, stdout, stderr

    """
    # 実行パスを生成
    exec_path = os.path.join(common_service.get_basepath(ws), pkg_name)
    # プロセスの停止忘れを防ぐため、稼働中の状態でRTCの一覧を取得する
    rtc_list, error_list = get_rtc_list(ws, pkg_name)

    if rtc_name is not None:
        # rtstop ⇒ rtexit ⇒ rtdel
        # rtstop
        code, stdout, stderr = deactivate_rtcs(ws, pkg_name)
        if code != 0:
            # エラーが発生した時点で処理を終了させる
            return (code, stdout, stderr)

        # rtexit
        if len(rtc_list) == 0:
            # 停止対象のコンポーネントが存在しない場合、終了する
            stderr = "No RT-Components to Stop"
            return (1, stdout, stderr)

        code, stdout, stderr = exit_rtc(rtc_list)
        if code != 0:
            # エラーが発生した時点で処理を終了させる
            return (code, stdout, stderr)

        # rtdel
        code, stdout, err_list = del_rtc(rtc_list)
        if len(err_list) == 0:
            stdout = "RT-Component Terminated"
        else:
            # エラーが発生した場合、ログに出力する
            logger.warning(err_list)
            stdout = "RT-Component Terminated, But some rtdel Commands are Failed."

        # 起動方法の判定
        check_rtc = f"mgr.py rtc run {rtc_name.rtc_name}"
        is_rtc = is_process(check_rtc)
        if is_rtc:
            # rtc run起動 指定されたRTCのプロセスをkillする
            kill_process(check_rtc)

        # 指定されたRTCが起動中のRTCの唯一のRTCの場合rtcdのプロセスもkillするためにsyetem terminateする
        if len(rtc_list) == 1 and rtc_name.rtc_name in rtc_list:
            terminate_system_packages(exec_path, pkg_name)

        return (code, stdout, "")

    else:
        code, stdout, stderr = terminate_system_packages(exec_path, pkg_name)
        kill_system_process(rtc_list)
        return (code, stdout, stderr)


def terminate_system_packages(path: str, pkg_name: str) -> Tuple[int, str, str]:
    """Del RTCs.

    system terminate -v

    Args:
        path(str): 実行パス
        pkg_name(str): パッケージ名

    Returns:
        Tuple[int, str, str]: code, stdout, stderr

    """
    stdout = ""
    options = [
        "system",
        "terminate",
        "-v",
    ]
    # カレントディレクトリを実行時にのみ変更する
    try:
        os.chdir(path)
        command = _generate_mgr_command(path, options)
        code, stdout, stderr = start_process_return_string(command)
        stdout = f"System Terminated in Package ({pkg_name})"
        os.chdir(home_dir)
    except FileNotFoundError:
        code = 1
        stderr = traceback.format_exc()

    return (code, stdout, stderr)


def get_rtc_list(ws: WS, pkg_name: str) -> Tuple[List[str], List[str]]:
    """Ls RTCs.

    rtls <PATH> -v

    Args:
        ws(WS): ワークスペース種別
        pkg_name(str): パッケージ名

    Returns:
        rtc_list: RTCコンポーネント一覧

    """
    rtc_list = []
    host, error_list = common_service.get_rts_host(ws, pkg_name)
    # 取得したホストから、rtlsコマンドでネームサービス上のコンポーネントを取得する
    for path_uri in host:
        options = [
            "rtls",
            path_uri,
            "-v",
        ]
        command = _generate_command(options)
        code, stdout, stderr = start_process_return_string(command)
        # 稼働しているコンポーネントの一覧化する
        if code == 0 and stdout:
            rtc_list.append(path_uri)
        else:
            # エラーの場合はログ出力のみ行う
            logger.warning(stderr)

    return (rtc_list, error_list)


def kill_system_process(rtc_list: List[str]) -> None:
    """システムのプロセスの停止を行う.

    Args:
        rtc_list(List[str]): RTCリスト

    """
    # systemとrtcのプロセスが残っていたら、killする
    kill_process("mgr.py run system")
    for rtc in rtc_list:
        start_str = rtc.rfind("/")
        end_str = rtc.find(".rtc")
        if start_str > 0 and end_str > 0:
            del_rtc_name = rtc[start_str + 1 : end_str - 1]
            kill_process(del_rtc_name)


def is_process(proc_name: str) -> bool:
    """対象のプロセスがあるかチェックする.

    Args:
        proc_name(str): プロセス名

    Returns:
        bool:判定結果(True:プロセスあり,False:プロセスなし)
    """
    for proc in psutil.process_iter(attrs=("name", "pid", "cmdline")):
        try:
            # コマンドライン引数が存在しない場合、チェック対象外としてスキップする
            if proc.info["cmdline"] is None:
                continue
            # 対象のプロセスがあるか引数となるRTC名からチェックする
            if proc_name in proc.info["cmdline"]:
                return True
        except psutil.AccessDenied:
            logger.warning(f"Process AccessDenied {proc}")

    return False


def kill_process(proc_name: str) -> None:
    """対象のプロセスをkillする.

    Args:
        proc_name(str): プロセス名

    """
    for proc in psutil.process_iter(attrs=("name", "pid", "cmdline")):
        try:
            # コマンドライン引数が存在しない場合、チェック対象外としてスキップする
            if proc.info["cmdline"] is None:
                continue
            # 対象のプロセスがあるか引数となるRTC名からチェックする
            if proc_name in proc.info["cmdline"]:
                p = psutil.Process(proc.pid)
                p.terminate()
                logger.info(f"Process Kill PID={proc.pid} PROC_NAME={proc_name}")
        except psutil.AccessDenied:
            pass
