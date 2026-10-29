"""コマンド実行モジュール."""
import getpass
import os
import subprocess
import sys
import time
import traceback
from typing import Any, List, Tuple

import chardet
import paramiko
import psutil

from ..config.config import WW_BASE_PATH


def start() -> None:
    """サーバ起動シェルスクリプトを実行する関数."""

    print("------------- Before server_launch.sh execution--------------")
    __print_process_list()

    shell = os.path.join(os.path.dirname(__file__), "../scripts/server_launch.sh")

    rtn = subprocess.run([shell], capture_output=True, shell=True)

    time.sleep(1)
    print("------------- After server_launch.sh execution --------------")
    __print_process_list()

    __print_subprocess_return(rtn)


def start_other_host() -> None:
    """sshで別hostに接続し、サーバ起動コマンドを実行する関数."""
    while True:
        try:
            print("Start a ssh connection.")
            HOSTNAME, USERNAME, PASSWORD = __ssh_connection_input()
        except:
            print("\nDone.")
            return

        COMMAND = "bash -lc 'wasanbon-webframework start'"

        # SSH接続
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # パスワード認証認証方式で接続
        try:
            client.connect(hostname=HOSTNAME, username=USERNAME, password=PASSWORD)
            # コマンド実行
            stdin, stdout, stderr = client.exec_command(COMMAND)

            for line in stdout:
                print(line)
            for line in stderr:
                print(line)

        except:
            print("[ERROR] ssh connection failed.", file=sys.stderr)
            traceback.print_exc()

        finally:
            client.close()
            del client, stdin, stdout, stderr


def ps() -> None:
    __print_process_list()


def kill(pid: str) -> int:
    def __on_terminate(proc: Any) -> None:
        print("process {} terminated with exit code {}".format(proc, proc.returncode))

    try:
        procs = psutil.Process(int(pid)).children()
    except:
        print("[ERROR] kill process faild")
        traceback.print_exc()
        return 1

    for p in procs:
        p.terminate()
    _, alive = psutil.wait_procs(procs, timeout=3, callback=__on_terminate)
    for p in alive:
        p.kill()

    try:
        p = psutil.Process(int(pid))
        p.terminate()
        p.kill()
    except:
        pass

    print("[SUCCESS] kill process " + pid + ".\n")
    return 0


def stop() -> None:
    """サーバ停止処理を実行する関数."""

    __print_process_list()
    while True:
        print("Enter the Process ID which you want to terminate. Press ctrl+c to quit...")
        try:
            pid_str = input("PID: ")
        except KeyboardInterrupt:
            print("\nDone.\n")
            break

        try:
            int(pid_str)
        except:
            print("Please input integer only")
            continue

        rtn_code = kill(pid_str)

        if rtn_code == 0:
            time.sleep(1)
            __print_process_list()


def stop_other_host() -> None:
    """sshで別hostに接続し、サーバ停止コマンドを実行する関数."""
    while True:
        try:
            print("Start a ssh connection.")
            HOSTNAME, USERNAME, PASSWORD = __ssh_connection_input()
        except:
            print("\nDone.\n")
            return

        # SSH接続
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # パスワード認証認証方式で接続
        try:
            client.connect(hostname=HOSTNAME, username=USERNAME, password=PASSWORD)
            # コマンド実行
            COMMAND = "bash -lc 'wasanbon-webframework ps'"
            stdin, stdout, stderr = client.exec_command(COMMAND)

            for line in stdout:
                print(line)
            for line in stderr:
                print(line)

            while True:
                print("Enter the Process ID which you want to terminate. Press ctrl+c to quit...")
                try:
                    pid_str = input("PID: ")
                except KeyboardInterrupt:
                    print("\nDone.\n")
                    break

                try:
                    int(pid_str)
                except:
                    print("Please input integer only")
                    continue

                # コマンド実行
                COMMAND = "bash -lc 'wasanbon-webframework pskill --pid '" + pid_str
                stdin, stdout, stderr = client.exec_command(COMMAND)

                for line in stdout:
                    print(line)
                for line in stderr:
                    print(line)

        except:
            print("[ERROR] ssh connection failed.")
            traceback.print_exc()

        finally:
            client.close()
            del client, stdin, stdout, stderr


def user_info_dist() -> None:
    """sftpで別hostに接続し、ユーザ設定ファイルを送る関数."""
    while True:
        try:
            HOSTNAME, USERNAME, PASSWORD = __ssh_connection_input()
        except:
            print("\nDone.")
            return
        # SSH接続
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # パスワード認証認証方式で接続
            client.connect(hostname=HOSTNAME, username=USERNAME, password=PASSWORD)

            # SFTPセッション開始
            sftp_connection = client.open_sftp()

            # リモートサーバーからローカルPCへファイルを転送
            user_file = os.path.join(WW_BASE_PATH, "user_info.yml")
            sftp_connection.put(user_file, ".wasanbon-webframework/user_info.yml")

        except:
            print("[ERROR] ssh connection failed.")
            traceback.print_exc()

        finally:
            client.close()


def __print_subprocess_return(rtn: Any) -> None:
    _stdout_encode = chardet.detect(rtn.stdout)
    stdout_encode = _stdout_encode["encoding"] if _stdout_encode["encoding"] is not None else "utf-8"
    _stderr_encode = chardet.detect(rtn.stderr)
    stderr_encode = _stderr_encode["encoding"] if _stderr_encode["encoding"] is not None else "utf-8"
    print(rtn.stdout.decode(stdout_encode))
    print(rtn.stderr.decode(stderr_encode), file=sys.stderr)


def __cmd_in_cmdlist(cmd: str, cmd_list: List[str]) -> bool:
    for cmd_i in cmd_list:
        if cmd in cmd_i:
            return True
    return False


def __print_process_list() -> None:
    print("[Proccess List]")
    print("------ uvicorn process list ------")
    print("PID".ljust(10), "COMMAND")
    for proc in psutil.process_iter():
        try:
            if "uvicorn" in proc.exe() or __cmd_in_cmdlist("uvicorn", proc.cmdline()):
                print(str(proc.pid).ljust(10), str(proc.cmdline()))
        except psutil.AccessDenied:
            pass
    print("")


def __ssh_connection_input() -> Tuple[str, str, str]:
    continue_or_not = input("Press Enter to continue. Press q to quit:")
    if continue_or_not == "q":
        raise KeyboardInterrupt("end of input")
    HOSTNAME = input("host: ")
    USERNAME = input("user: ")
    PASSWORD = getpass.getpass("pswd: ")
    return HOSTNAME, USERNAME, PASSWORD
